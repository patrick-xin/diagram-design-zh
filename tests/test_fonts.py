"""字体行为回归：只在临时目录生成字体和成品。"""
import base64
import contextlib
import importlib.util
import io
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]/'skills/diagram-design-zh'
sys.path.insert(0, str(ROOT/'scripts'))
import embed_fonts as fonts

try:
    from fontTools import subset
    from fontTools.ttLib import TTFont, TTCollection
except ImportError:
    subset = None


class FontTextTests(unittest.TestCase):
    def test_role_text_and_entities(self):
        source = """<style>:root{--font-sans:'Audit Sans','Noto Sans SC',sans-serif;
        --font-serif:'LXGW WenKai','Songti SC',serif;--font-mono:'Audit Mono',ui-monospace,monospace;}
        h1{font-family:var(--font-serif)}</style><h1>标题 &amp; café</h1>
        <svg><title>元数据</title><text font-family="'Noto Sans SC',sans-serif">μs · Москва</text>
        <text font-family="'Sarasa Mono SC',monospace">技术</text></svg><script>隐藏</script>"""
        source = fonts.sync_svg_stacks(source)
        chars = fonts.TextCollector(source).chars
        self.assertTrue(set('标题&é') <= chars['serif'])
        self.assertTrue(set('μМ') <= chars['sans'])
        self.assertTrue(set('技术') <= chars['mono'])
        self.assertFalse(set('元数据隐藏') & set().union(*chars.values()))

    def test_sync_preserves_geometry_ids_and_other_attributes(self):
        source = """<style>:root{--font-sans:'New','Noto Sans SC',sans-serif;}</style>
        <svg viewBox="0 0 1000 360"><desc>示例 font-family='MiSans'</desc><!-- font-family='MiSans' -->
        <text id="keep-id" data-font-family="leave"
        x="12" y="24" fill="#29314f" font-family="'MiSans', 'Noto Sans SC',sans-serif">节点</text></svg>"""
        updated = fonts.sync_svg_stacks(source)
        self.assertIn('data-font-family="leave"', updated)
        self.assertIn("<desc>示例 font-family='MiSans'</desc>",updated)
        self.assertIn("<!-- font-family='MiSans' -->",updated)
        def strip(s): return fonts.FAMILY_ATTR_RE.sub('', s)
        self.assertEqual(strip(source),strip(updated))
        self.assertIn('New', re.search(r'<text.*?</text>',updated,re.S).group())
        self.assertEqual(updated, fonts.sync_svg_stacks(updated))

    def test_motion_status_can_use_its_dynamic_text_without_system_fonts(self):
        source='<body><svg><g data-motion-item aria-label="恢复完成"><text>节点</text></g></svg><script data-diagram-controls>status.textContent="就绪";</script></body>'
        chars=fonts.TextCollector(source).chars
        self.assertTrue(set('恢复完成就绪') <= chars['sans'])
        self.assertTrue(set('恢复完成就绪') <= chars['mono'])

    def test_replacing_serif_head_keeps_a_referenced_embedded_fallback(self):
        source="<style>:root { --font-serif: 'Audit Title', 'Songti SC', 'SimSun', serif; }</style><svg><text font-family=\"'Noto Serif SC', 'Songti SC', serif\">标题</text></svg>"
        updated=fonts.sync_svg_stacks(fonts.ensure_embedded_fallbacks(source))
        names=fonts.families(fonts.read_stacks(updated)['serif'])
        self.assertEqual(names,['Audit Title','Noto Serif SC','Songti SC','SimSun','serif'])
        self.assertIn('Noto Serif SC',updated.split('<svg>')[1])
        self.assertEqual(updated,fonts.ensure_embedded_fallbacks(updated))

    def test_comma_inside_family_name(self):
        self.assertEqual(fonts.families(" 'Audit, Family', 'Fallback', sans-serif"),['Audit, Family','Fallback','sans-serif'])


@unittest.skipIf(subset is None, 'fonttools + brotli required')
class EmbeddedFontTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        cls.paths=[]
        for weight in (400,600):
            font=TTFont(ROOT/'fonts/noto-sans-sc-400.woff2')
            tool=subset.Subsetter(); tool.populate(text='节点标题技术éμМABC ');tool.subset(font)
            for record in font['name'].names:
                if record.nameID in (1,16): record.string='Audit Sans'.encode(record.getEncoding())
            font['OS/2'].usWeightClass=weight
            path=cls.dir/f'custom-{weight}.woff2';font.save(path);font.close();cls.paths.append(path)
        collection=TTCollection();collection.fonts=[TTFont(p) for p in cls.paths]
        for font in collection.fonts:font.flavor=None
        cls.ttc=cls.dir/'custom.ttc';collection.save(cls.ttc);collection.close()

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def source(self,head='Audit Sans'):
        return f"""<html><head><style>:root{{--font-sans:'{head}','Noto Sans SC',sans-serif;
        --font-serif:'Noto Serif SC','Songti SC',serif;--font-mono:'Sarasa Mono SC','Noto Sans SC',ui-monospace,monospace;}}
        h1{{font-family:var(--font-serif)}}.bold{{font-weight:600}}</style></head><body><h1>标题</h1>
        <svg><text font-family="'MiSans','Noto Sans SC',sans-serif" font-weight="600">节点 é μ М</text></svg></body></html>"""

    def test_real_faces_and_fallback_coverage(self):
        source=fonts.sync_svg_stacks(self.source())
        block,_,_=fonts.build_block(subset,source,self.paths)
        text='\n'.join(block)
        self.assertIn("font-family: 'Audit Sans'; font-style: normal; font-weight: 600;",text)
        self.assertIn("font-family: 'Noto Sans SC';",text)
        encoded=re.search(r"font-family: 'Audit Sans';.*?base64,([^)]*)",text).group(1)
        with TTFont(io.BytesIO(base64.b64decode(encoded))) as font:
            self.assertTrue({ord(c) for c in '节点éμМ'} <= set(font.getBestCmap()))

    def test_mismatch_does_not_alias_wrong_font(self):
        faces=[face for p in self.paths for face in fonts.probe_faces(p)]
        with patch.object(fonts,'_SYSTEM_INDEX',{}):
            notices=[];result=fonts.resolve_custom('Wrong Family',faces,notices)
        self.assertEqual(result,[]);self.assertTrue(notices)

    def test_system_family_is_excluded_before_explicit_match(self):
        faces=[fonts.FontFace(self.paths[0],'PingFang SC',400)]
        notices=[];self.assertEqual(fonts.resolve_custom('PingFang SC',faces,notices),[])
        self.assertTrue(notices)

    def test_recursive_collection_discovery(self):
        directory=self.dir/'nested/fonts';directory.mkdir(parents=True,exist_ok=True)
        (directory/'custom.ttc').write_bytes(self.ttc.read_bytes())
        with patch.object(fonts,'SYS_FONT_DIRS',[self.dir/'nested']),patch.object(fonts,'_SYSTEM_INDEX',None):
            found=fonts.system_index()['audit sans']
            self.assertEqual({f.weight for f in found},{400,600})
            encoded=fonts.build_face(subset,found[1],'节点')
            with TTFont(io.BytesIO(base64.b64decode(encoded))) as font:
                self.assertEqual(font['OS/2'].usWeightClass,600)

    def test_custom_mono_embeds_and_keeps_cjk_fallback(self):
        source=self.source('MiSans').replace("'Sarasa Mono SC'","'Audit Sans'").replace("<svg>","<svg><text font-family=\"'Sarasa Mono SC',monospace\">技术</text>")
        block,_,_=fonts.build_block(subset,fonts.sync_svg_stacks(source),self.paths)
        self.assertIn("font-family: 'Audit Sans';",'\n'.join(block))
        self.assertIn("font-family: 'Noto Sans SC';",'\n'.join(block))

    def test_idempotence_and_legacy_strip(self):
        path=self.dir/'diagram.html';path.write_text(self.source())
        with contextlib.redirect_stdout(io.StringIO()):
            fonts.process(path,subset,False,self.paths); first=path.read_bytes()
            fonts.process(path,subset,False,self.paths); self.assertEqual(first,path.read_bytes())
            path.write_text(path.read_text().replace('fonts:begin 字体子集','fonts:begin 思源字体子集'))
            fonts.process(path,None,True,[])
        self.assertNotIn('fonts:begin',path.read_text())


if __name__=='__main__': unittest.main()
