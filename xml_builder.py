#xml_builder.py
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Mapping, Optional
from xml.dom import minidom

from config import cfg

def build_xml(data: Mapping[str, dict], output_file: Optional[str] = None):
    output_file = output_file or cfg.output.xml_file

    root = ET.Element(
            'Message', {
                    'xsi:noNamespaceSchemaLocation': 'schema.xsd',
                    'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                }
        )

    container = ET.SubElement(root, 'VerificationMeasuringInstrumentData')

    for cert_num, val in data.items():
        vmi = ET.SubElement(container, 'VerificationMeasuringInstrument')

        ET.SubElement(vmi, 'NumberVerification').text = cert_num

        if val.get('ver_date'):
            ET.SubElement(vmi, 'DateVerification').text = val['ver_date']

        result_ver = 2
        if val.get('valid_date'):
            ET.SubElement(vmi, 'DateEndVerification').text = val['valid_date']
            result_ver = 1

        ET.SubElement(vmi, 'TypeMeasuringInstrument').text = val.get('mit_title') or ''

        employees = ET.SubElement(vmi, 'ApprovedEmployees')
        name = ET.SubElement(employees, 'Name')
        ET.SubElement(name, 'Last').text = val['last']
        ET.SubElement(name, 'First').text = val['first']
        ET.SubElement(employees, 'SNILS').text = val['snils']

        ET.SubElement(vmi, 'ResultVerification').text = str(result_ver)

    ET.SubElement(root, 'SaveMethod').text = '2'

    rough = ET.tostring(root, encoding='unicode')
    pretty = minidom.parseString(rough).toprettyxml(indent=' ', encoding=None)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty)
            
