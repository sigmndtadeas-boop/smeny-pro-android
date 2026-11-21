from pathlib import Path

p = Path("smeny_pro_mobile_build/www/index.html")
s = p.read_text(encoding="utf-8")

marker = "smeny-pro-modal-actions-top"
if marker in s:
    print("Top modal action layout already applied.")
    raise SystemExit(0)

if "</head>" not in s:
    raise SystemExit("Cannot find </head>; refusing to patch.")

css = r"""
/* Směny PRO – keep every modal confirmation/action row at the top */
<style id="smeny-pro-modal-actions-top">
.modal {
  display: flex !important;
  flex-direction: column !important;
  overflow: hidden !important;
}
.modalhead {
  order: 0 !important;
  flex: 0 0 auto !important;
  position: relative;
  z-index: 3;
}
#modalFoot {
  order: 1 !important;
  display: flex !important;
  flex: 0 0 auto !important;
  position: relative !important;
  top: auto !important;
  bottom: auto !important;
  justify-content: flex-start !important;
  flex-wrap: wrap;
  padding: 10px 16px !important;
  border-top: 0 !important;
  border-bottom: 1px solid var(--line) !important;
  background: var(--panel, #fff) !important;
  z-index: 2;
}
#modalFoot:empty {
  display: none !important;
}
#modalBody {
  order: 2 !important;
  flex: 1 1 auto !important;
  min-height: 0 !important;
  overflow-y: auto !important;
  overscroll-behavior: contain;
}
#modalHeadActions {
  flex-wrap: wrap;
  justify-content: flex-end;
}
#modalFoot button,
#modalHeadActions button {
  min-height: 40px;
}
@media (max-width: 700px) {
  .modal {
    max-height: 94vh !important;
  }
  #modalFoot {
    padding: 9px 12px !important;
    gap: 8px !important;
  }
  #modalFoot button {
    flex: 0 1 auto;
  }
}
</style>
"""
s = s.replace("</head>", css + "\\n</head>", 1)
p.write_text(s, encoding="utf-8")
print("All modal footer actions are now displayed directly below the modal title, above the scrollable content.")
