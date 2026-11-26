"""``xml:lang`` is an ``xs:language`` code in every model (P2.3).

Before 0.3.0 only ODM 2.0 checked it: ODM 1.3.2, CT-XML, Define-XML and ARM used a
plain string, and ODM 1.3.2 ``Presentation`` wrote ``lang=`` without the ``xml:``
prefix its schema requires.
"""
import importlib
import xml.etree.ElementTree as ET
from unittest import TestCase

import odmlib.mode as mode
import odmlib.odm_1_3_2.model as ODM
from odmlib.exceptions import OdmlibValidationError
from odmlib.odm_parser import ODMSchemaValidator

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
MODELS = ("odm_1_3_2", "odm_2_0", "define_2_0", "define_2_1", "arm_1_0", "ct_1_1_1")


def _translated_text(name, lang):
    model = importlib.import_module(f"odmlib.{name}.model")
    extra = {"Type": "text/plain"} if name == "odm_2_0" else {}   # required in 2.0
    return model.TranslatedText(_content="t", lang=lang, **extra)


class TestTranslatedTextLang(TestCase):

    def test_valid_codes_accepted_in_every_model(self):
        for name in MODELS:
            for code in ("en", "en-US", "zh-Hant-TW", "x-klingon"):
                with self.subTest(model=name, code=code):
                    self.assertEqual(_translated_text(name, code).lang, code)

    def test_invalid_codes_rejected_in_every_model(self):
        for name in MODELS:
            for code in ("en_US", "english language", "", "toolongsubtag1", "-en"):
                with self.subTest(model=name, code=code):
                    with self.assertRaises(OdmlibValidationError) as ctx:
                        _translated_text(name, code)
                    self.assertEqual(ctx.exception.attribute, "lang")

    def test_permissive_mode_still_accepts_invalid_codes(self):
        with mode.permissive():
            self.assertEqual(ODM.TranslatedText(_content="t", lang="en_US").lang, "en_US")

    def test_written_with_xml_prefix(self):
        element = ODM.TranslatedText(_content="t", lang="en").to_element()
        self.assertEqual(element.get(XML_LANG), "en")


class TestPresentationLang(TestCase):

    def test_presentation_writes_xml_lang(self):
        presentation = ODM.Presentation(OID="PR.1", lang="en", _content="stylesheet")
        element = presentation.to_element()
        self.assertEqual(element.get(XML_LANG), "en")
        self.assertIsNone(element.get("lang"))
        self.assertIn('xml:lang="en"', presentation.to_xml_string())

    def test_presentation_validates_against_the_odm_1_3_2_xsd(self):
        presentation = ODM.Presentation(OID="PR.1", lang="en", _content="stylesheet")
        schema = ODMSchemaValidator(standard="odm", version="1.3.2").xsd
        errors = list(schema.iter_errors(presentation.to_element()))
        self.assertEqual(errors, [])

    def test_presentation_rejects_invalid_code(self):
        with self.assertRaises(OdmlibValidationError):
            ODM.Presentation(OID="PR.1", lang="en_US")

    def test_presentation_round_trips_through_the_loader(self):
        import odmlib.odm_loader as OL
        xml = ODM.Presentation(OID="PR.1", lang="fr", _content="css").to_xml_string()
        loader = OL.XMLODMLoader(model_package="odm_1_3_2")
        loaded = loader.load_document(ET.fromstring(xml))
        self.assertEqual(loaded.lang, "fr")
