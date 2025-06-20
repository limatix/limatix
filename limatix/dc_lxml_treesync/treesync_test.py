from lxml import etree
import dc_lxml_treesync as treesync
import pdb

Orig=r"""
<foo fiddle="faddle">
  <bar name="bar1">fubar</bar>
  <fubar>bar</fubar>
</foo>
"""

A=r"""
<foo fiddle="faddle">
  <fubar>bar</fubar>
  <bar name="bar1">foobar</bar>
</foo>
"""

B=r"""
<foo fiddle="faddle">
  <bar name="bar2">fubar</bar>
  <fubar>BAR</fubar>
</foo>
"""


tree_orig=etree.XML(Orig)
tree_A=etree.XML(A)
tree_B=etree.XML(B)
maxmergedepth=10

tree_merged=treesync.treesync(tree_orig,tree_A,tree_B,maxmergedepth)

print(etree.tostring(tree_merged,pretty_print=True,encoding='utf-8').decode('utf-8'))

tree_merged2=treesync.treesync_multi(tree_orig,[tree_A,tree_B],maxmergedepth)

print(etree.tostring(tree_merged2,pretty_print=True,encoding='utf-8').decode('utf-8'))
