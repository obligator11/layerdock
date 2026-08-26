import io
from xml.sax.saxutils import escape

from docx import Document
from docx.shared import Emu
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

from backend.pdf_parser import parse_pdf

EMU_PER_PT = 12700
_next_id = [1]


def _pt_to_emu(pt):
    return int(pt * EMU_PER_PT)


def _rgb_hex(rgb):
    return "%02X%02X%02X" % tuple(rgb)


def _textbox_xml(x_pt, y_pt, w_pt, h_pt, text, font, size_pt, color_rgb):
    _next_id[0] += 1
    shape_id = _next_id[0]
    x, y = _pt_to_emu(x_pt), _pt_to_emu(y_pt)
    cx, cy = max(_pt_to_emu(w_pt), 1), max(_pt_to_emu(h_pt), 1)
    half_pts = max(int(size_pt * 2), 2)
    color = _rgb_hex(color_rgb)
    safe_text = escape(text)
    safe_font = escape(font or "Calibri")

    xml = f"""
    <w:r {nsdecls('w')}>
      <w:drawing xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">
        <wp:anchor distT="0" distB="0" distL="0" distR="0" simplePos="0"
                   relativeHeight="{shape_id}" behindDoc="0" locked="0"
                   layoutInCell="1" allowOverlap="1">
          <wp:simplePos x="0" y="0"/>
          <wp:positionH relativeFrom="page"><wp:posOffset>{x}</wp:posOffset></wp:positionH>
          <wp:positionV relativeFrom="page"><wp:posOffset>{y}</wp:posOffset></wp:positionV>
          <wp:extent cx="{cx}" cy="{cy}"/>
          <wp:wrapNone/>
          <wp:docPr id="{shape_id}" name="TextBox{shape_id}"/>
          <wp:cNvGraphicFramePr/>
          <a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
            <a:graphicData uri="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">
              <wps:wsp xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">
                <wps:cNvSpPr txBox="1"/>
                <wps:spPr>
                  <a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
                  <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
                  <a:noFill/>
                  <a:ln><a:noFill/></a:ln>
                </wps:spPr>
                <wps:txbx>
                  <w:txbxContent>
                    <w:p>
                      <w:pPr><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>
                      <w:r>
                        <w:rPr>
                          <w:rFonts w:ascii="{safe_font}" w:hAnsi="{safe_font}"/>
                          <w:sz w:val="{half_pts}"/>
                          <w:color w:val="{color}"/>
                        </w:rPr>
                        <w:t xml:space="preserve">{safe_text}</w:t>
                      </w:r>
                    </w:p>
                  </w:txbxContent>
                </wps:txbx>
                <wps:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" anchor="t">
                  <a:noAutofit/>
                </wps:bodyPr>
              </wps:wsp>
            </a:graphicData>
          </a:graphic>
        </wp:anchor>
      </w:drawing>
    </w:r>
    """
    return parse_xml(xml)


def _picture_anchor_xml(x_pt, y_pt, w_pt, h_pt, rel_id):
    _next_id[0] += 1
    shape_id = _next_id[0]
    x, y = _pt_to_emu(x_pt), _pt_to_emu(y_pt)
    cx, cy = max(_pt_to_emu(w_pt), 1), max(_pt_to_emu(h_pt), 1)

    xml = f"""
    <w:r {nsdecls('w')}>
      <w:drawing xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">
        <wp:anchor distT="0" distB="0" distL="0" distR="0" simplePos="0"
                   relativeHeight="{shape_id}" behindDoc="0" locked="0"
                   layoutInCell="1" allowOverlap="1">
          <wp:simplePos x="0" y="0"/>
          <wp:positionH relativeFrom="page"><wp:posOffset>{x}</wp:posOffset></wp:positionH>
          <wp:positionV relativeFrom="page"><wp:posOffset>{y}</wp:posOffset></wp:positionV>
          <wp:extent cx="{cx}" cy="{cy}"/>
          <wp:wrapNone/>
          <wp:docPr id="{shape_id}" name="Picture{shape_id}"/>
          <wp:cNvGraphicFramePr/>
          <a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
            <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
              <pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
                <pic:nvPicPr>
                  <pic:cNvPr id="{shape_id}" name="Picture{shape_id}"/>
                  <pic:cNvPicPr/>
                </pic:nvPicPr>
                <pic:blipFill>
                  <a:blip r:embed="{rel_id}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>
                  <a:stretch><a:fillRect/></a:stretch>
                </pic:blipFill>
                <pic:spPr>
                  <a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
                  <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
                </pic:spPr>
              </pic:pic>
            </a:graphicData>
          </a:graphic>
        </wp:anchor>
      </w:drawing>
    </w:r>
    """
    return parse_xml(xml)


def build_docx(pdf_path: str, output_path: str, progress_cb=None) -> dict:
    _next_id[0] = 1
    parsed = parse_pdf(pdf_path)
    doc = Document()

    for i, page in enumerate(parsed["pages"]):
        section = doc.sections[0] if i == 0 else doc.add_section()
        section.page_width = Emu(_pt_to_emu(page["width"]))
        section.page_height = Emu(_pt_to_emu(page["height"]))
        section.left_margin = section.right_margin = Emu(0)
        section.top_margin = section.bottom_margin = Emu(0)

        anchor_paragraph = doc.add_paragraph()

        # Images (raster + rasterized vector graphics) first, text drawn on top
        for img in page["images"]:
            try:
                img_bytes = img["raw_bytes"]
                image_part, rel_id = anchor_paragraph.part.get_or_add_image(io.BytesIO(img_bytes))
                x0, y0, x1, y1 = img["bbox"]
                run_elem = _picture_anchor_xml(x0, y0, x1 - x0, y1 - y0, rel_id)
                anchor_paragraph._p.append(run_elem)
            except Exception:
                continue

        for block in page["text_blocks"]:
            x0, y0, x1, y1 = block["bbox"]
            run_elem = _textbox_xml(
                x0, y0, max(x1 - x0, 4), max(y1 - y0, block["size"] * 1.3),
                block["text"], block["font"], block["size"], block["color"],
            )
            anchor_paragraph._p.append(run_elem)

        if progress_cb:
            progress_cb(i + 1, parsed["page_count"])

    doc.save(output_path)
    return {"page_count": parsed["page_count"], "output_path": output_path}