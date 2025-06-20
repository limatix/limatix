dc_lxml_treesync
----------------
dc_lxml_treesync is a component of LIMATIX datacollect2

datacollect2 stores experiment logs in XML, which have the advantage
of being both human readable and machine readable. Since experimental
processes rarely happen perfectly, it is occasionally necessary
to manually edit an experiment log or filled checklist to make
a correction. We don't want to have to quit out completely of
datacollect2 in order to make such a change.

So resynchronization after a manual change (or perhaps a programmatic
change from other software) to an XML file is necessary. Unfortunately,
since the document structure can change arbitrarily this is a
non-trivial problem. 

For the most part, datacollect2 keeps itself synchronized with
on-disk checklists and experiment logs by using canonicalized
xpaths to find the locations of XML elements and structures that
have in memory copies that need to be kept synchronized with the
on disk copy. See the canonical_path module for more information.
As long as what is kept synchronized are multiple single elements,
for which an update is effectively complete replacement, such
an approach works very well, subject to the sufficiency of the
canonicalized paths for re-identifying the correct object.

If the items to be synchronized are themselves compound XML structures,
and especially if different pieces of this compound structure might
be modified simultaneously (one piece modified on disk, another modified
in memory) then merging these changes becomes less critical. That is
the problem solved by dc_lxml_treesync.

dc_lxml_treesync provides a means to merge changed XML trees,
which are (possibly) modified copies of an original. It can
be thought of as an "n-way diff" for XML tree structures.
It is built on the xpath canonicalization infrastructure provided
by the canonicalize_path module.

How to use:

Assume python lxml etrees: tree_orig, tree_a, and tree_b are the
original, modification "A" and modification "B" trees.

maxmergedepth is an integer indicating for how many layers of depth
recursive merges should be performed (as opposed to strict comparison/replacement)

ignore_blank_text is a flag (default True) that says to ignore whitespace t
ext nodes.  tag_index_paths_override allows you to provide a dictionary
of tag index paths which will be passed on to the canonicalize_path xpath
routines so as to help identify elements by content rather than strictly position. 

Call the function treesync():
  treesync(tree_orig,tree_a,tree_b,maxmergedepth,ignore_blank_text=True,tag_index_paths_override=None)
treesync() returns the merged tree or raises SyncError() or MultiChangeError() exceptions

If you have more than two child trees, provide a list of child trees and call
treesync_multi() instead:
  treesync_multi(tree_orig,treelist,maxmergedepth,ignore_blank_text=True,tag_index_paths_override=None)




Acknowledgments
---------------
Thanks to the LIMATIX proposal team for their input and support:
  Hui Hu, Iowa State University
  Amy Kaleita, Iowa State University 
  Brian Mennecke, Iowa State University  1960-2016 RIP
  Hridesh Rajan, Iowa State University
  Michael Thompson, Cornell University

Thanks also to Dave Forsyth and Carl Magnuson of TRI-Austin
for their input and support. 

Thanks to Joseph Hynek for providing the RF survey data used in the
ProcessTrak example. 

This material is based on work supported by the Air Force Research
Laboratory under Contract #FA8650-10-D-5210, Task Order #023 and
performed at Iowa State University; Case number 88ABW-2016-4385

