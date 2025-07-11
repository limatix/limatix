# This processtrak step will add in an explicit ordering of your
# elements. Use it in your .prx file as a step:
# <prx:step name="create_random_order">
#   <order random="true"/>
#   <script name="limatix_create_order.py"/>
# </prx:step>
from limatix.dc_value import integervalue

def run(_xmldoc,_element,_index):
    return { "dc:order": integervalue(_index) }
