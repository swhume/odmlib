from unittest import TestCase
import odmlib.odm_1_3_2.model as ODM
import json


class TestRangeCheck(TestCase):
    def setUp(self) -> None:
        attrs = self._set_attributes()
        self.range_check = ODM.RangeCheck(**attrs)

    def test_add_check_value(self):
        self.range_check.CheckValue = [ODM.CheckValue(_content="DIABP")]
        self.assertEqual(self.range_check.CheckValue[0]._content, "DIABP")

    def test_add_formal_expression(self):
        self.range_check.FormalExpression = [ODM.FormalExpression(Context="Python 3.7", _content="print('hello world')")]
        self.assertEqual(self.range_check.FormalExpression[0]._content, "print('hello world')")

    def test_add_measurement_unit_ref(self):
        self.range_check.MeasurementUnitRef = ODM.MeasurementUnitRef(MeasurementUnitOID="ODM.MU.UNITS")
        self.assertEqual(self.range_check.MeasurementUnitRef.MeasurementUnitOID, "ODM.MU.UNITS")

    def test_add_error_message(self):
        #self.range_check.ErrorMessage = ODM.ErrorMessage()
        self.range_check.ErrorMessage.TranslatedText.append(ODM.TranslatedText(_content="invalid test code", lang="en"))
        self.range_check.ErrorMessage.TranslatedText.append(ODM.TranslatedText(_content="code de test invalide", lang="fr"))
        self.assertEqual(len(self.range_check.ErrorMessage.TranslatedText), 2)
        self.assertEqual(self.range_check.ErrorMessage.TranslatedText[1]._content, 'code de test invalide')

    def test_to_json(self):
        attrs = self._set_attributes()
        rc = ODM.RangeCheck(**attrs)
        rc.CheckValue = [ODM.CheckValue(_content="DIABP")]
        rc.FormalExpression = [ODM.FormalExpression(Context="Python 3.7", _content="print('hello world')")]
        rc.MeasurementUnitRef = ODM.MeasurementUnitRef(MeasurementUnitOID="ODM.MU.UNITS")
        # commented out when allowed empty wrapper ELEMENTS to be virtually instantiated (may not keep this)
        #rc.ErrorMessage = ODM.ErrorMessage()
        rc.ErrorMessage.TranslatedText.append(ODM.TranslatedText(_content="invalid test code", lang="en"))
        rc.ErrorMessage.TranslatedText.append(ODM.TranslatedText(_content="code de test invalide", lang="fr"))
        rc_json = rc.to_json()
        rc_dict = json.loads(rc_json)
        print(rc_dict)
        self.assertDictEqual(rc_dict, self._json_range_check_dict())

    def test_to_dict(self):
        attrs = self._set_attributes()
        rc = ODM.RangeCheck(**attrs)
        rc.CheckValue = [ODM.CheckValue(_content="DIABP")]
        rc.FormalExpression = [ODM.FormalExpression(Context="Python 3.7", _content="print('hello world')")]
        rc.MeasurementUnitRef = ODM.MeasurementUnitRef(MeasurementUnitOID="ODM.MU.UNITS")
        rc.ErrorMessage.TranslatedText.append(ODM.TranslatedText(_content="invalid test code", lang="en"))
        rc.ErrorMessage.TranslatedText.append(ODM.TranslatedText(_content="code de test invalide", lang="fr"))
        rc_dict = rc.to_dict()
        print(rc_dict)
        rc_dict = rc.to_dict()
        self.assertDictEqual(rc_dict, self._json_range_check_dict())

    def test_to_xml(self):
        attrs = self._set_attributes()
        rc = ODM.RangeCheck(**attrs)
        rc.CheckValue = [ODM.CheckValue(_content="DIABP")]
        rc.FormalExpression = [ODM.FormalExpression(Context="Python 3.7", _content="print('hello world')")]
        rc.MeasurementUnitRef = ODM.MeasurementUnitRef(MeasurementUnitOID="ODM.MU.UNITS")
        #rc.ErrorMessage = ODM.ErrorMessage()
        rc.ErrorMessage.TranslatedText.append(ODM.TranslatedText(_content="invalid test code", lang="en"))
        rc.ErrorMessage.TranslatedText.append(ODM.TranslatedText(_content="code de test invalide", lang="fr"))
        rc_xml = rc.to_xml()
        self.assertEqual(rc_xml.attrib["SoftHard"], "Soft")

    def _set_attributes(self):
        """
        set some RangeCheck element attributes using test data
        :return: dictionary with RangeCheck attribute information
        """
        return {"Comparator": "EQ", "SoftHard": "Soft"}

    def _json_range_check_dict(self):
        return {'Comparator': 'EQ', 'SoftHard': 'Soft', 'CheckValue': [{'_content': 'DIABP'}], 'FormalExpression':
            [{'Context': 'Python 3.7', '_content': "print('hello world')"}],
            'MeasurementUnitRef': {'MeasurementUnitOID': 'ODM.MU.UNITS'},
            'ErrorMessage': {'TranslatedText': [{'lang': 'en', '_content': 'invalid test code'},
                             {'lang': 'fr', '_content': 'code de test invalide'}]}
                }
