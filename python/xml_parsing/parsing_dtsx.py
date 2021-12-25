import xml.etree.ElementTree as ET
tree = ET.parse('CreateSalesForecastInput.dtsx')
root = tree.getroot()
results=[]
for i in root.iter('property'): 
    if 'name' in i.attrib.keys():
        results.append(
            {
                "name":i.attrib['name']
                ,"Description":i.attrib['description']
            }
        )
""
# :
    # print(str(i.find('name')))