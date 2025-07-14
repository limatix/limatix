# This processtrak step will add in an explicit ordering of your
# elements. Use it in your .prx file as a step:
# <prx:step name="create_random_order">
#   <prx:order random="true"/>
#   <prx:script name="limatix_create_order.py"/>
# </prx:step>

# Then, in subsequent steps:
#  <prx:step name="...">
#    <prx:order select="dc:order" sort="numeric"/>
#    ...
#  </prx:step>

from limatix.dc_value import integervalue

def run(_xmldoc,_element,_index):
    return { "dc:order": integervalue(_index) }
