#test_xml_builder.py
import xml.etree.ElementTree as ET

from xml_builder import build_xml


def _sample_data():
    return {
            'С-КД/23-09-2026/560743690': {
                    'ver_date': '2026-09-23',
                    'valid_date': '2032-09-22',
                    'mit_title': 'Water mits',
                    'last': 'Фамилия',
                    'first': 'Имя',
                    'snils': '00000000000',
                },
        }


def test_build_xml_valid(tmp_path):
    out = tmp_path / 'out.xml'
    build_xml(_sample_data(), str(out))

    root = ET.parse(out).getroot()
    assert root.tag == 'Message'

    vmi = root.find('.//VerificationMeasuringInstrument')
    assert vmi.findtext('NumberVerification') == 'С-КД/23-09-2026/560743690'
    assert vmi.findtext('DateVerification') == '2026-09-23'
    assert vmi.findtext('DateEndVerification') == '2032-09-22'
    assert vmi.findtext('TypeMeasuringInstrument') == 'Water mits'
    assert vmi.findtext('ResultVerification') == '1'


def text_result_verification_is_2_without_valid_date(tmp_path):
    data = _sample_data()
    data['С-КД/23-09-2026/560743690']['valid_date'] = None

    out = tmp_path / 'out.xml'
    build_xml(data, str(out))

    vmi = ET.parse(out).getroot().find('.//VerificationMeasuringInstrument')
    assert vmi.find('DateEndVerification') is None
    assert vmi.findtext('ResultVerification') == '2'


def test_save_method_is_2(tmp_path):
    out = tmp_path / 'out.xml'
    build_xml(_sample_data(), str(out))

    root = ET.parse(out).getroot()
    assert root.findtext('.//ApprovedEmployees/Name/Last') == 'Фамилия'
    assert root.findtext('.//ApprovedEmployees/Name/First') == 'Имя'
    assert root.findtext('.//ApprovedEmployees/SNILS') == '00000000000'
    
