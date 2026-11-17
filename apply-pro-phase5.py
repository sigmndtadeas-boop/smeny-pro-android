from pathlib import Path
import json, re

root = Path("smeny_pro_mobile_build")
html = root / "www" / "index.html"
s = html.read_text(encoding="utf-8")
if "export-bridge.bundle.js" not in s:
    marker = "<script>\nconst $="
    if marker not in s:
        raise SystemExit("Main application script marker not found")
    s = s.replace(marker, '<script src="export-bridge.bundle.js"></script>\n' + marker, 1)

old = "function download(content,name,type){let blob=new Blob([content],{type}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;a.click();URL.revokeObjectURL(url)}"
new = """function bytesToBase64(bytes){let binary='';for(let i=0;i<bytes.length;i+=0x8000)binary+=String.fromCharCode(...bytes.subarray(i,i+0x8000));return btoa(binary)}
async function download(content,name,type,isBase64=false){
 const native=!!(window.Capacitor&&typeof window.Capacitor.isNativePlatform==='function'&&window.Capacitor.isNativePlatform());
 if(native){
  try{
   if(!window.SmenyExportFile||typeof window.SmenyExportFile.save!=='function')throw new Error('Nativní ukládání není dostupné.');
   const data=isBase64?content:bytesToBase64(new TextEncoder().encode(String(content)));
   const result=await window.SmenyExportFile.save({fileName:name,mimeType:type,data});
   toast('Soubor uložen: '+(result.fileName||name));return result;
  }catch(e){const msg=String(e&&e.message||e);toast(msg.toLowerCase().includes('zrušil')?'Ukládání bylo zrušeno.':'Soubor se nepodařilo uložit: '+msg);return null}
 }
 let blob;
 if(isBase64){const raw=atob(content),bytes=new Uint8Array(raw.length);for(let i=0;i<raw.length;i++)bytes[i]=raw.charCodeAt(i);blob=new Blob([bytes],{type})}
 else blob=new Blob([content],{type});
 const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);toast('Soubor je připraven ke stažení.');
}"""
if old in s:
    s = s.replace(old, new, 1)
elif "async function download(content,name,type,isBase64=false)" not in s:
    raise SystemExit("Download helper not found")

s = s.replace("function exportCSV(){", "async function exportCSV(){", 1)
s = s.replace(";toast('CSV export připraven.')}", "}", 1)
s = s.replace("function exportJSON(){download(JSON.stringify(db,null,2),", "async function exportJSON(){await download(JSON.stringify(db,null,2),", 1)
s = s.replace(";toast('Záloha stažena.')}", "}", 1)
s = s.replace("XLSX.writeFile(wb,'smeny-'+prefix+'.xlsx',{compression:true});\n  toast('Excelová tabulka je připravena ke stažení.');", "const excelBase64=XLSX.write(wb,{bookType:'xlsx',type:'base64',compression:true});\n  await download(excelBase64,'smeny-'+prefix+'.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',true);", 1)

html.write_text(s, encoding="utf-8")
(root / "export-bridge.js").write_text("import { registerPlugin } from '@capacitor/core';\nwindow.SmenyExportFile = registerPlugin('ExportFile');\n", encoding="utf-8")

config = json.loads((root / "capacitor.config.json").read_text(encoding="utf-8"))
package = config.get("appId", "cz.smenypro.app")
java = """package PACKAGE_NAME;
import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.util.Base64;
import com.getcapacitor.ActivityResult;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.ActivityCallback;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.OutputStream;

@CapacitorPlugin(name = "ExportFile")
public class ExportFilePlugin extends Plugin {
    @PluginMethod
    public void save(PluginCall call) {
        String fileName = call.getString("fileName");
        String mimeType = call.getString("mimeType", "application/octet-stream");
        String data = call.getString("data");
        if (fileName == null || fileName.trim().isEmpty() || data == null) {
            call.reject("Chybí název souboru nebo jeho obsah.");
            return;
        }
        Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType(mimeType);
        intent.putExtra(Intent.EXTRA_TITLE, fileName);
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
        startActivityForResult(call, intent, "handleSaveResult");
    }
    @ActivityCallback
    private void handleSaveResult(PluginCall call, ActivityResult result) {
        if (call == null) return;
        if (result.getResultCode() != Activity.RESULT_OK || result.getData() == null || result.getData().getData() == null) {
            call.reject("Uživatel zrušil ukládání souboru.");
            return;
        }
        Uri uri = result.getData().getData();
        String data = call.getString("data");
        String fileName = call.getString("fileName", "soubor");
        try (OutputStream output = getContext().getContentResolver().openOutputStream(uri, "w")) {
            if (output == null) throw new IllegalStateException("Nelze otevřít cílový soubor.");
            output.write(Base64.decode(data, Base64.DEFAULT));
            output.flush();
            JSObject ret = new JSObject();
            ret.put("uri", uri.toString());
            ret.put("fileName", fileName);
            call.resolve(ret);
        } catch (Exception ex) {
            call.reject("Zápis souboru selhal: " + ex.getMessage(), ex);
        }
    }
}
""".replace("PACKAGE_NAME", package)

main_files = list((root / "android/app/src/main/java").rglob("MainActivity.java"))
if len(main_files) != 1:
    raise SystemExit(f"Expected one MainActivity.java, found {len(main_files)}")
main = main_files[0]
(main.parent / "ExportFilePlugin.java").write_text(java, encoding="utf-8")
ms = main.read_text(encoding="utf-8")
if "registerPlugin(ExportFilePlugin.class)" not in ms:
    if "import android.os.Bundle;" not in ms:
        ms = ms.replace("import com.getcapacitor.BridgeActivity;", "import android.os.Bundle;\nimport com.getcapacitor.BridgeActivity;")
    pattern = r"public class MainActivity extends BridgeActivity\s*\{\s*\}"
    replacement = """public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(ExportFilePlugin.class);
        super.onCreate(savedInstanceState);
    }
}"""
    if re.search(pattern, ms):
        ms = re.sub(pattern, replacement, ms, count=1)
    else:
        idx = ms.rfind("}")
        if idx < 0:
            raise SystemExit("Could not patch MainActivity.java")
        ms = ms[:idx] + """    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(ExportFilePlugin.class);
        super.onCreate(savedInstanceState);
    }
""" + ms[idx:]
    main.write_text(ms, encoding="utf-8")

print("Phase 5: Android Save As export support added.")
