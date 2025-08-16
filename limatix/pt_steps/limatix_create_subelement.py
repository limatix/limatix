# This processtrak step will add in Sub elements with the given tag and attribute. Matching pre-existing sub-elements will be replaced.
# Use it in your .prx file as a step:
# <prx:step name="create_subelement">
#   <prx:script name="limatix_create_subelement.py"/>
#   <prx:param name="tagname">dc:subel</prx:param>
#   <prx:param name="measident_xpath">concat(dc:measident,'subname')</prx:param>
#   <prx:param name="attributename">subtype</prx:param>
#   <prx:param name="attributevalue_xpath">subname</prx:param>
# </prx:step>

import collections
from limatix.xmldoc import xmldoc
from limatix.dc_value import xmltreevalue

def run(_xmldoc,_element,tagname_str,measident_xpath_str=None,attributename_str=None, attributevalue_xpath_str=None):
    new_doc = xmldoc.newdoc(tagname_str,nsmap=_xmldoc.nsmap)
    if measident_xpath_str is not None:
        measident_el = new_doc.addelement(new_doc.getroot(),"dc:measident")
        new_doc.settext(measident_el,_xmldoc.xpathsinglecontextstr(_element,measident_xpath_str))
        pass
    new_attr_dict = collections.OrderedDict()
    if attributename_str is not None and attributevalue_xpath_str is not None:
        new_attr_dict[attributename_str] = _xmldoc.xpathsinglecontextstr(_element,attributevalue_xpath_str)
        pass
    new_element = xmltreevalue(new_tree)
    return [ ((tagname_str,new_attr_dict), new_element) ]
