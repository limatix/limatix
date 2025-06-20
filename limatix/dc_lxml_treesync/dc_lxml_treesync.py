import copy
import sys
import array
from lxml import etree
try :
    import canonicalize_path
    pass
except ImportError:
    from limatix import canonicalize_path
    pass


try: 
    import builtins  # python3
    pass
except ImportError: 
    import __builtin__ as builtins # python2
    pass


if not hasattr(builtins,"basestring"):
    basestring=str  # python3
    pass


def childlist(element,ignore_blank_text):
    # Create list of children of element, including text nodes
    # Note that because we don't modify the children, the text nodes
    # we append are redundant with element.text and the tail attribute of each child
    elems=[]

    partialpaths=[]
    priortextcount=0

    # add in attributes, each as its own dictionary
    for attrname in element.attrib.keys():
        elems.append({attrname: element.attrib[attrname]})
        partialpaths.append("@%s" % (attrname))
        pass

    if element.text is not None and (not ignore_blank_text or not element.text.isspace()):  # text node for main text


        # sys.stderr.write("id(element.text)=%d\n" % (id(element.text)))
        # sys.stderr.write("id(element.text)=%d\n" % (id(element.text)))
        textnode=element.text
        elems.append(textnode)
        partialpaths.append("text()[%d]" % (priortextcount+1))
        # sys.stderr.write("id(textnode)=%d\n" % (id(textnode)))
        # sys.stderr.write("id(list entry)=%d\n" % (id(elems[-1])))
        
        priortextcount+=1

        pass

    # enumerate non-text elements
    elems.extend([ elem for elem in element.iterchildren() ])
    partialpaths.extend([ None for elem in element.iterchildren() ]) # not-text elements get blank path, so far -- to be added by element_to_etxpath() later 

        

    # add in text nodes for tail nodes
    pos=0
    while pos < len(elems):
        if not isinstance(elems[pos],basestring) and not isinstance(elems[pos],dict):
            if elems[pos].tail is not None and (not ignore_blank_text or not elems[pos].tail.isspace()):
                elems.insert(pos+1,elems[pos].tail)
                partialpaths.insert(pos+1,"text()[%d]" % (priortextcount+1))
                priortextcount+=1
                pass
            pass
        pos+=1
        pass
    
    return (partialpaths,elems)


class instruction(object):
    insttype=None  # type: IT_...
    path=None
    path2=None
    # element=None

    IT_ADD=1  # path is path of element added (in tree a or b), path2 is predecessor (or None)
    IT_DELETE=2 # path is path of element deleted (in orig tree); path2 is predecessor (or None)
    IT_RECONCILE=3 # path is path of element to be reconciled. 
    IT_INTERCHANGE=4 # path and path2 are paths of elements in orig tree to interchange


    def __init__(self,insttype,path,path2=None):
        self.insttype=insttype
        self.path=path
        self.path2=path2
        pass
    pass


def findpredecessor(modifiedpathlist,path):

    index=modifiedpathlist.index(path)-1
    if index < 0:
        return None
        pass
    else: 
        return modifiedpathlist[index]
    pass


def buildinstructions(origpathlist,modifiedpathlist):
    # return a set of instructions for transforming 
    # origpathlist into modifiedpathlist
    
    origpathset=set(origpathlist)
    modifiedpathset=set(modifiedpathlist)

    # since paths should be unique, set length should match list length
    assert(len(origpathset)==len(origpathlist))
    assert(len(modifiedpathset)==len(modifiedpathlist))

    # Deleted is a list of deleted paths 
    deleted=[ path for path in origpathlist if path not in modifiedpathlist ]

    # Added is a list of added paths
    added=[ path for path in modifiedpathlist if path not in origpathlist ] 

    # kept is a list of 
    # elements that are kept, ordered by origpathlist
    kept=[ path for path in origpathlist if path in modifiedpathlist ]

    # kept is a list of 
    # elements that are kept, ordered by modifiedpathlist
    modifiedkept=[ path for path in modifiedpathlist if path in origpathlist ]

    # We represent the reordering of the kept elements by 
    # a permutation. This permutation can be expressed 
    # as a set of disjoint cycles

    # see also http://stackoverflow.com/questions/2987605/minimum-number-of-swaps-needed-to-change-array-1-to-array-2

    permutation = list(map(dict((path, index) for index, path in enumerate(kept)).get, modifiedkept))

    # identify disjoint cycles
    seen=set([])
    cycles=[]

    for permidx in range(len(permutation)):
        if permidx in seen: 
            # if this index has been seen before, it has already been 
            # included in a cycle
            continue
        cycle=[]
        cyclemember=permidx
        cycle.append(cyclemember)
        while permutation[cyclemember] != permidx:
            cyclemember=permutation[cyclemember]
            seen.add(cyclemember)
            cycle.append(cyclemember)
            pass
        cycles.append(cycle)
        pass
        

    # represent each cycle as a product of transpositions
    # based on http://math.stackexchange.com/questions/319979/how-to-write-permutations-as-product-of-disjoint-cycles-and-transpositions
    # if cycle = (1,3,4,6,7,9)
    # then transpositions = (1,3)(3,4)(4,6)(6,7)(7,9)
    transpositions=[]
    for cycle in cycles: 
        for cnt in range(len(cycle)-1):
            transpositions.append((cycle[cnt],cycle[cnt+1]))
            pass
        pass
    
    # Build instruction list 

    instructions=[]
    # Start with deletions
    instructions.extend([ instruction(instruction.IT_DELETE, path, findpredecessor(origpathlist,path)) for path in deleted]) 
    
    # Now add transpositions
    permuted=copy.copy(kept)  # permuted starts as a simple copy
    for transposition in transpositions:
        instructions.append(instruction(instruction.IT_INTERCHANGE,permuted[transposition[0]],permuted[transposition[1]]))
        # interchange elements in permuted
        permuted[transposition[0]],permuted[transposition[1]] = permuted[transposition[1]],permuted[transposition[0]]
        pass
    # now permuted should match modifiedkept
    assert(modifiedkept==permuted)

    # now add additions
    instructions.extend([ instruction(instruction.IT_ADD, path, findpredecessor(modifiedpathlist,path)  ) for path in added]) 
    

    # mark all kept elements to be reconciled
    instructions.extend([ instruction(instruction.IT_RECONCILE, path) for path in kept]) 


    return instructions

def element_to_etxpath(root,parent,element,partialpath,tag_index_paths_override=None):
    # like getelementetxpath, but returns creates proper paths
    # for text node elements that are strings and for 
    # attributes, which show up as dictionaries

    # import pdb;pdb.set_trace()

    # for text and attribute nodes, path information already encoded in partialpath
    
    if isinstance(element,basestring):
        # return path of the form .../text()[index]
        parentpath=canonicalize_path.getelementetxpath(None,parent,root=root,tag_index_paths_override=tag_index_paths_override)
        
        return "%s/%s" % (parentpath,partialpath)
    elif isinstance(element,dict):
        # create a path of the form .../@name
        parentpath=canonicalize_path.getelementetxpath(None,parent,root=root,tag_index_paths_override=tag_index_paths_override)

        #priortextcount=0
        #if parent.text is not None:
        #    priortextcount+=1
        #    pass
        
        return "%s/%s" % (parentpath,partialpath)

    # ... otherwise
    return canonicalize_path.getelementetxpath(None,element,root=root,tag_index_paths_override=tag_index_paths_override)

class SyncError(BaseException):
    value=None
    def __init__(self,value):
        self.value=value
        pass
    def __str__(self):
        return "SyncError: %s" % (str(self.value))
        
    pass


class MultiChangeError(BaseException):
    value=None
    def __init__(self,value):
        self.value=value
        pass
    def __str__(self):
        return "MultiChangeError: %s" % (str(self.value))
        
    pass


def instruction_path_used(instrs, path):

    using_instrs = []
    
    for instr in instrs: 
        if instr.insttype==instruction.IT_ADD:
            if instr.path==path or instr.path2==path: # 11/29/2019 -- do we really need to check against path2 (predecessor)? ... probably not. 
                using_instrs.append(instr)
            pass
        elif instr.insttype==instruction.IT_DELETE:
            if instr.path==path: 
                using_instrs.append(instr)
            pass
        elif instr.insttype==instruction.IT_INTERCHANGE:
            if instr.path==path or instr.path2==path:
                using_instrs.append(instr)
            pass
            
        pass
    if len(using_instrs)==0:
        return None
    return using_instrs

def check_instruction_conflict(instrs_list):
    need_to_check = []

    for treeindex in range(len(instrs_list)):
        instrs_listelem=instrs_list[treeindex]

        for instr in instrs_listelem:

            need_to_check.append((treeindex,instr))
            pass
        pass
    
    while len(need_to_check) > 0:
        (treeindex,instr)=need_to_check.pop()

        
        if instr.insttype==instruction.IT_ADD: 
            for treeindex2 in range(len(instrs_list)):
                if treeindex2==treeindex:
                    continue
                if instruction_path_used(instrs_list[treeindex2],instr.path) is not None:
                    raise SyncError("Path %s referenced in multiple trees" % (instr.path))
                        
                #if instruction_path_used(instrs_list[treeindex2],instr.path2) is not None:
                # 11/29/2019 -- should be OK because path2 is merely used to specify the predecessor. Means that if elements are added in both trees after some element,
                # the additional element from one of the trees will
                # have a different predecessor, but that should be OK
                #    raise SyncError("Path %s referenced in multiple trees" % (instr.path2))
                pass
            pass
        elif instr.insttype==instruction.IT_DELETE:
            for treeindex2 in range(len(instrs_list)):
                if treeindex2==treeindex:
                    continue
                using_instrs = instruction_path_used(instrs_list[treeindex2],instr.path)
                if using_instrs is None:
                    using_instrs=[]
                    pass

                problematic_instr=None
                for using_instr in using_instrs:
                    if using_instr.insttype==instruction.IT_ADD and using_instr.path != instr.path:
                        # This instruction is using our deleted element at most as a predecessor. Just reprogram the instruction to point at predecessor of this element
                        using_instr.path2 = instr.path2
                        # .. but using_instr has been modified so it needs to be rechecked
                        need_to_check.append((treeindex2,using_instr))
                        pass
                    elif using_instr.insttype==instruction.IT_DELETE:
                        # element also deleted in other tree... not a problem
                        pass
                    else:
                        assert(using_instr.insttype==instruction.IT_INTERCHANGE)
                        # this would be a problem
                        problematic_instr=using_instr
                        pass
                    pass
                    
                if problematic_instr is not None:
                    raise SyncError("Path %s deleted in tree, used in another tree" % (instr.path))
                pass
            pass
        elif instr.insttype==instruction.IT_INTERCHANGE:
            for treeindex2 in range(len(instrs_list)):
                if treeindex2==treeindex:
                    continue
                if instruction_path_used(instrs_list[treeindex2],instr.path) is not None:
                    raise SyncError("Path %s reordered in one tree, referenced in a second" % (instr.path))
                if instruction_path_used(instrs_list[treeindex2],instr.path2) is not None:
                    raise SyncError("Path %s reordered in tree A, referenced in tree B" % (instr.path2))
                pass
            pass
        pass
        
    #for instr in instrs_a: 
    #    if instr.insttype==instruction.IT_ADD:
    #        if instruction_path_used(instrs_b,instr.path) is not None:
    #            raise SyncError("Path %s referenced in both trees" % (instr.path))
    #
    #        if instruction_path_used(instrs_b,instr.path2) is not None:
    #            raise SyncError("Path %s referenced in both trees" % (instr.path2))
    #
    #        pass
    #    elif instr.insttype==instruction.IT_DELETE:
    #        if instruction_path_used(instrs_b,instr.path) is not None:
    #            raise SyncError("Path %s deleted in tree A, referenced in tree B" % (instr.path))
    #        pass
    #    elif instr.insttype==instruction.IT_INTERCHANGE:
    #        if instruction_path_used(instrs_b,instr.path) is not None:
    #            raise SyncError("Path %s reordered in tree A, referenced in tree B" % (instr.path))
    #        if instruction_path_used(instrs_b,instr.path2) is not None:
    #            raise SyncError("Path %s reordered in tree A, referenced in tree B" % (instr.path2))
    #            
    #            # instruction_path_used(instrs_b,instr.path2):
    #        pass
    #    pass
    pass


def treesmatch(tree_a,tree_b,ignore_blank_text):
    if tree_a.text != tree_b.text:
        return False

    if tree_a.tag !=tree_b.tag:
        return False

    (partialpaths_a,treeelems_a) = childlist(tree_a,ignore_blank_text)
    (partialpaths_b,treeelems_b) = childlist(tree_b,ignore_blank_text)

    if len(treeelems_a) != len(treeelems_b):
        return False

    for elcnt in range(len(treeelems_a)):
        el_a=treeelems_a[elcnt]
        el_b=treeelems_b[elcnt]

        if isinstance(el_a,basestring):
            if not isinstance(el_b,basestring):
                return False
            if el_a != el_b:
                return False
            pass
        elif isinstance(el_a,dict):
            if not isinstance(el_b,dict):
                return False
            if list(el_a.keys()) != list(el_b.keys()):
                return False
            #key=el_a.keys()[0]
            key=next(iter(el_a))  # return first key
            if el_a[key] != el_b[key]: 
                return False
            pass
        else : 
            # child element
            if not treesmatch(el_a,el_b,ignore_blank_text):
                return False
            pass

        pass
    return True




def tree_add_elements(tree,treeelems):
    # add treeelems to tree
    # NOTE: Actual elements in treeelems list get inserted into tree and thus modified!

    partialpaths=[]
    previoustextnodes=0
    prevel=None

    for treeelcnt in range(len(treeelems)):
        elem=treeelems[treeelcnt]
        partialpaths.append(None) # will overwrite this new element below

        if isinstance(elem,basestring):
            # text node
            if prevel is None:
                if tree.text is None:
                    tree.text=""
                    pass
                tree.text+=elem
            else :
                if prevel.tail is None:
                    prevel.tail=""
                    pass
                prevel.tail+=elem
                pass
            partialpaths[treeelcnt]="text()[%d]" % (previoustextnodes+1)
            previoustextnodes+=1
            pass
        elif isinstance(elem,dict):
            keys=list(elem.keys())
            assert(len(keys)==1)
            tree.attrib[keys[0]]=elem[keys[0]]
            partialpaths[treeelcnt]="@%s" % (keys[0])
            pass
        else : 
            # elem is an element
            assert(elem.tail is None) # tail assigned in later iterations of this loop
            tree.append(elem)
            prevel=elem
            partialpaths[treeelcnt]=None
            pass

        pass
    return partialpaths


def check_paths_match(root_tag,treeelems,treepaths,tag_index_paths_override,ignore_root_tag_name=False):
    # raise exception if treepaths don't correspond to treeelems
    # Do this by forming a tree from copies of treeelems
    # then extracting its paths, and comparing with treepaths. 

    tree_test=etree.Element(root_tag)
    treeelems_copy=copy.deepcopy(treeelems)
    treeelems_partialpaths=tree_add_elements(tree_test,treeelems_copy)
    
    treepaths_compare=[element_to_etxpath(tree_test,tree_test,elem,partialpath,tag_index_paths_override=tag_index_paths_override) for partialpath,elem in zip(treeelems_partialpaths,treeelems_copy) ]

    assert(len(treepaths_compare)==len(treepaths))


    if ignore_root_tag_name:
        # Convert treepaths_compare and treepaths to remove first element
        treepaths_compare = [ canonicalize_path.canonical_etxpath_join(*([""]+canonicalize_path.canonical_etxpath_split(treepaths_compare[cnt])[2:])) for cnt in range(len(treepaths)) ]

        treepaths = [ canonicalize_path.canonical_etxpath_join(*([""] + canonicalize_path.canonical_etxpath_split(treepaths[cnt])[2:])) for cnt in range(len(treepaths)) ]
        pass
    
    for cnt in range(len(treepaths)):
        if treepaths_compare[cnt] != treepaths[cnt]:
            raise SyncError("check_paths_match: Original path %s has changed to new path %s" % (treepaths[cnt],treepaths_compare[cnt]))
        pass

    pass


def perform_instructions(root_tag,treeelems_new,treepaths_new,treeelems,treepaths,instructions,tag_index_paths_override,ignore_root_tag_name):
    for instruction in instructions: 
        if instruction.insttype==instruction.IT_ADD: 
            pathtoadd=instruction.path
            pathpredecessor=instruction.path2
            
            treeindex=treepaths.index(pathtoadd)
            elemtoadd=treeelems[treeindex]
            
            predecessorindex=-1
            if pathpredecessor is not None:
                predecessorindex=treepaths_new.index(pathpredecessor)
                pass
            
            addelem=copy.deepcopy(elemtoadd)
            if hasattr(addelem,"tail"):
                addelem.tail=None # remove tail text, if present (separately handled)
                pass
            
            treeelems_new.insert(predecessorindex+1,addelem)
            treepaths_new.insert(predecessorindex+1,pathtoadd)
            pass
        elif instruction.insttype==instruction.IT_DELETE:
            pathtodelete=instruction.path
            deleteindex=treepaths_new.index(pathtodelete)
            del treepaths_new[deleteindex]
            del treeelems_new[deleteindex]
            pass
        elif instruction.insttype==instruction.IT_RECONCILE: 
            # Reconciliation happens in a later phase so do nothing now
            pass
        elif instruction.insttype==instruction.IT_INTERCHANGE:
            path1=instruction.path
            path2=instruction.path2

            index1=treepaths_new.index(path1)
            index2=treepaths_new.index(path2)
            
            elem1=treeelems_new[index1]
            elem2=treeelems_new[index2]
            
            # swap!
            treeelems_new[index1]=elem2
            treeelems_new[index2]=elem1
            treepaths_new[index1]=path2
            treepaths_new[index2]=path1
            pass
        
        check_paths_match(root_tag,treeelems_new,treepaths_new,tag_index_paths_override,ignore_root_tag_name=ignore_root_tag_name)

        pass


    pass

def findchanged(origelem,treeelems_list,treepaths_list,path):
    # origelem is the element from the original tree
    # treeelems_list is a list of (element lists) for (possibly) changed trees. 
    # treepaths_list is a list of (list of paths) for the elements in the (possibly) changed trees 
    # path is the path to find an element in these trees. 
    # the element should have changed in no more than one of the trees. 
    # if so, return (index_into_treelemens_list_of_tree_with_changed_element,changed_element)
    # if not, return (None,None)
    # if more than one has changed, raise MultiChangeError
    #
    # The element may be an etree.Element, a dict (representing attribute entry), or a string (representing text node)
    
    compareelems=[]
    
    for treeindex in range(len(treeelems_list)):
        treeelem_listelem=treeelems_list[treeindex]
        treeelem_listelemidx=treepaths_list[treeindex].index(path)
        treeelem_listelemelem=treeelems_list[treeindex][treeelem_listelemidx]
        compareelems.append(treeelem_listelemelem)
        pass
        
    # Create array showing which element match (equality)
    matcharray=array.array('B')
    for treeindex in range(len(treeelems_list)):

        if isinstance(origelem,basestring):
            # text node
            matcharray.append(origelem==compareelems[treeindex])
            pass
        elif isinstance(origelem,dict):
            # attribute

            # Dict should have only a single entry and 
            # its key should be consistent

            assert(len(origelem.keys())==1)
            assert(len(compareelems[treeindex].keys())==1)
            #assert(list(origelem.keys())[0]==list(compareelems[treeindex].keys())[0])
            assert(next(iter(origelem))==next(iter(compareelems[treeindex])))

            #key=origelem.keys()[0]
            key=next(iter(origelem))

            matcharray.append(origelem[key]==compareelems[treeindex][key])
            pass
        else: 
            # element
            # Compare serializations
            origstr=etree.tostring(origelem)
            comparestr=etree.tostring(compareelems[treeindex])
            matcharray.append(origstr==comparestr)
            
            pass
        pass
    if matcharray.count(1) == len(treeelems_list):
        return (None,None) # all match each other
        
    if matcharray.count(0)==1:
        return (matcharray.index(0),compareelems[matcharray.index(0)])

    # Otherwise then no unique change was found. 
    # Raise an exception... but first, determine message
    Msg="Orig = %s" % (origelem)
    for treeindex in range(len(treeelems_list)):
        if matcharray[treeindex]==0: 
            Msg +=" ; Tree %d = %s" % (treeindex,compareelems[treeindex])
            pass
        pass
    
    raise MultiChangeError(Msg) 


def reconcile(treeelems_orig,treepaths_orig,treeelems_new,treepaths_new,treeelems_list,treepaths_list,instructions_list,maxmergedepth,ignore_blank_text,tag_index_paths_override):


    # identify set of treepaths that need reconciliation, 
    # Reconciliation is needed in elements that were kept in both 
    # trees. 

    # toreconcile_b=set([])
    # for instruction in instructions_b:
    #     if instruction.insttype==instruction.IT_RECONCILE:
    #        toreconcile_b.add(instruction.path)
    #        pass
    #     pass


    toreconcile_list=[]

    for treeindex in range(len(treeelems_list)):
        
        toreconcile_listelem=set([])
    
        for instruction in instructions_list[treeindex]:
            if instruction.insttype==instruction.IT_RECONCILE:
                toreconcile_listelem.add(instruction.path)
                pass
            pass
        toreconcile_list.append(toreconcile_listelem)
        
        pass


    # toreconcile is the intersection (AND) of all of the elements in each that need reconciliation

    # toreconcile = toreconcile_a & toreconcile_b # intersection of A and B
    toreconcile = toreconcile_list[0]
    for treeindex in range(1,len(treeelems_list)):
        toreconcile=toreconcile & toreconcile_list[treeindex]
        pass

    # Go through each treepath and attempt to reconcile
    for path in toreconcile: 

        #print("Reconcile %s" % (path))
        
        # find original element
        origidx=treepaths_orig.index(path)
        origelem=treeelems_orig[origidx]

        # find new element
        newidx=treepaths_new.index(path)
        # newelem=treeelems_new[newidx]

        ## find element in modified tree A
        #aidx=treepaths_a.index(path)
        #aelem=treeelems_a[aidx]

        ## find element in modified tree B
        #bidx=treepaths_b.index(path)
        #belem=treeelems_b[bidx]
            

        if isinstance(origelem,etree._Element) and maxmergedepth > 1 and "Comment" not in type(origelem).__name__:
            # recursive call to treesync
            subtreeelems=[]
            for treeindex in range(len(treeelems_list)):
                treeelem_listelem=treeelems_list[treeindex]
                treeelem_listelemidx=treepaths_list[treeindex].index(path)
                treeelem_listelemelem=treeelems_list[treeindex][treeelem_listelemidx]
                subtreeelems.append(treeelem_listelemelem)
                pass

            treeelems_new[newidx]=treesync_multi(origelem,subtreeelems,maxmergedepth-1,ignore_blank_text,tag_index_paths_override=tag_index_paths_override)
            pass
        else : 
            try : 
                (treeindex,newelem)=findchanged(origelem,treeelems_list,treepaths_list,path)
                if treeindex is None: 
                    # Nothing changed; do nothing
                    pass
                else: 
                    # assign changed value to new tree
                    treeelems_new[newidx]=copy.deepcopy(newelem)                    
                    pass
                pass
            except MultiChangeError as e: 
                raise SyncError("Path %s has changed inconsistently. %s" % (path,e.value))
                
        #if isinstance(origelem,basestring):
            ## text node
            #if origelem==aelem and origelem==belem: 
            #    # nothing changed
            #    pass
            #elif origelem==aelem and origelem != belem:
            #    # tree b has changed
            #    treeelems_new[newidx]=copy.deepcopy(belem)
            #    pass
            #elif origelem==belem and origelem != aelem:
            #    # tree a has changed
            #    treeelems_new[newidx]=copy.deepcopy(aelem)
            #    pass
            #else: 
            #    # both changed. Cannot reconcile
            #    raise SyncError("Path %s is a text node that has changed inconsistently. Orig=\"%s\" A=\"%s\" B=\"%s\"." % (path,origelem,aelem,belem))
            #pass
        #elif isinstance(origelem,dict):
        #    # attribute
        #
        #    # Dict should have only a single entry and 
        #    # its key should be consistent
        #    assert(len(origelem.keys())==1)
        #    assert(len(aelem.keys())==1)
        #    assert(len(belem.keys())==1)
        #    assert(list(origelem.keys())[0]==list(aelem.keys())[0])
        #    assert(list(origelem.keys())[0]==list(belem.keys())[0])
        #
        #    key=list(origelem.keys())[0]
        #    
        #    if origelem[key]==aelem[key] and origelem[key]==belem[key]:
        #        # nothing changed
        #        pass
        #    elif origelem[key]==aelem[key] and origelem[key] != belem[key]:
        #        # tree b has changed
        #        treeelems_new[newidx]=copy.deepcopy(belem)
        #        pass
        #    elif origelem[key]==belem[key] and origelem[key] != aelem[key]:
        #        # tree a has changed
        #        treeelems_new[newidx]=copy.deepcopy(aelem)
        #        pass
        #    else: 
        #        # both changed. Cannot reconcile
        #        raise SyncError("Path %s is an attribute node that has changed inconsistently. Orig=\"%s\" A=\"%s\" B=\"%s\"." % (path,origelem[key],aelem[key],belem[key]))
        #
        #    pass
        #else: 
        #    # element
        #    if maxmergedepth > 1:
        #        # recursive call to treesync
        #        treeelems_new[newidx]=treesync(origelem,aelem,belem,maxmergedepth-1,ignore_blank_text,tag_index_paths_override=tag_index_paths_override)
        #    else :
        #        # Compare serializations
        #        origstr=etree.tostring(origelem)
        #        astr=etree.tostring(aelem)
        #        bstr=etree.tostring(belem)
        #        
        #        if origstr==astr and origstr==bstr:
        #            # don't need to do anything...treelems_new[newidx] is already a copy of origelem
        #            pass
        #        elif origstr==astr and origstr != bstr: 
        #            # bstr has changed... copy belem
        #            treeelems_new[newidx]=copy.deepcopy(belem)
        #            pass
        #        elif origstr==bstr and origstr != astr: 
        #            # astr has changed... copy aelem
        #            treeelems_new[newidx]=copy.deepcopy(aelem)
        #            pass
        #        else: 
        #            # both changed. Cannot reconcile
        #            raise SyncError("Path %s is beyond maxmergedepth and has changed inconsistently. Orig=\"%s\" A=\"%s\" B=\"%s\"." % (path,origstr,astr,bstr))
        #        pass
        #    pass
        pass
    pass


def treesync(tree_orig,tree_a,tree_b,maxmergedepth,ignore_blank_text=True,tag_index_paths_override=None,ignore_root_tag_name=False):
    if tree_orig.tag != tree_a.tag or tree_orig.tag != tree_b.tag:
        raise SyncError("tree tag mismatch: %s vs. %s vs. %s" % (tree_orig.tag,tree_a.tag,tree_b.tag))
        
    
    # enumerate elements in orig
    (partialpaths_orig,treeelems_orig)=childlist(tree_orig,ignore_blank_text)

    # enumerate elements in a
    (partialpaths_a,treeelems_a)=childlist(tree_a,ignore_blank_text)

    # enumerate elements in b
    (partialpaths_b,treeelems_b)=childlist(tree_b,ignore_blank_text)
    

    # get paths for orig
    treepaths_orig=[ element_to_etxpath(tree_orig,tree_orig,elem,partialpath,tag_index_paths_override=tag_index_paths_override) for (partialpath,elem) in zip(partialpaths_orig,treeelems_orig) ]

    # get paths for tree a
    treepaths_a=[ element_to_etxpath(tree_a,tree_a,elem,partialpath,tag_index_paths_override=tag_index_paths_override) for (partialpath,elem) in zip(partialpaths_a,treeelems_a) ]

    # get paths for tree b
    treepaths_b=[ element_to_etxpath(tree_b,tree_b,elem,partialpath,tag_index_paths_override=tag_index_paths_override) for (partialpath,elem) in zip(partialpaths_b,treeelems_b) ]

    # determine mapping from orig to a
    instructions_a=buildinstructions(treepaths_orig,treepaths_a)
    instructions_b=buildinstructions(treepaths_orig,treepaths_b)

    check_instruction_conflict([instructions_a,instructions_b])
        

    nsmap=dict(tree_orig.nsmap)
    nsmap.update(tree_a.nsmap)
    nsmap.update(tree_b.nsmap)
    # NOTE: If we wanted we could extract nsmaps from all children here
    # too. Probably not all that useful, though
    
    tree_new=etree.Element(tree_orig.tag,nsmap=nsmap)
    
    # create list for new element
    treeelems_new=[ copy.deepcopy(orig_el) for orig_el in treeelems_orig ]

    # clear out redundant tail text 
    for element in treeelems_new: 
        if hasattr(element,"tail"):
            element.tail=None
            pass
        pass

    treepaths_new=copy.deepcopy(treepaths_orig)

    perform_instructions(tree_orig.tag,treeelems_new,treepaths_new,treeelems_a,treepaths_a,instructions_a,tag_index_paths_override,ignore_root_tag_name)
    perform_instructions(tree_orig.tag,treeelems_new,treepaths_new,treeelems_b,treepaths_b,instructions_b,tag_index_paths_override,ignore_root_tag_name)

    reconcile(treeelems_orig,treepaths_orig,treeelems_new,treepaths_new,[treeelems_a,treeelems_b],[treepaths_a,treepaths_b],[instructions_a,instructions_b],maxmergedepth,ignore_blank_text,tag_index_paths_override=tag_index_paths_override)

    # add treeelems_new to tree_new
    # import pdb;pdb.set_trace()

    tree_add_elements(tree_new,treeelems_new)
    return tree_new


                


def treesync_multi(tree_orig,treelist,maxmergedepth,ignore_blank_text=True,tag_index_paths_override=None,ignore_root_tag_name=False):

    if len(treelist)==0:
        return copy.deepcopy(tree_orig)


    if not ignore_root_tag_name: 
        for treeindex in range(len(treelist)):
            if tree_orig.tag != treelist[treeindex].tag:
                raise SyncError("tree tag mismatch: %s vs. %s" % (tree_orig.tag,treelist[treeindex].tag))
            pass
        pass
    
    
    # enumerate elements in orig
    (partialpaths_orig,treeelems_orig)=childlist(tree_orig,ignore_blank_text)

    # enumerate elements in each tree
    partialpaths_list=[]
    treeelems_list=[]
    for treeindex in range(len(treelist)):
        (partialpaths_listelem,treeelems_listelem)=childlist(treelist[treeindex],ignore_blank_text)
        partialpaths_list.append(partialpaths_listelem)
        treeelems_list.append(treeelems_listelem)
        pass

    ## enumerate elements in b
    #(partialpaths_b,treeelems_b)=childlist(tree_b,ignore_blank_text)
    

    # get paths for orig
    treepaths_orig=[ element_to_etxpath(tree_orig,tree_orig,elem,partialpath,tag_index_paths_override=tag_index_paths_override) for (partialpath,elem) in zip(partialpaths_orig,treeelems_orig) ]

    # get paths for each tree
    treepaths_list=[]

    for treeindex in range(len(treelist)):
        treepaths_listelem=[ element_to_etxpath(treelist[treeindex],treelist[treeindex],elem,partialpath,tag_index_paths_override=tag_index_paths_override) for (partialpath,elem) in zip(partialpaths_list[treeindex],treeelems_list[treeindex]) ]
        treepaths_list.append(treepaths_listelem)
        pass

    # # get paths for tree b
    # treepaths_b=[ element_to_etxpath(tree_b,tree_b,elem,partialpath,tag_index_paths_override=tag_index_paths_override) for (partialpath,elem) in zip(partialpaths_b,treeelems_b) ]



    # determine mapping from orig to each tree
    # instructions_a=buildinstructions(treepaths_orig,treepaths_a)
    instructions_list=[]

    for treeindex in range(len(treelist)):
        instructions_listelem=buildinstructions(treepaths_orig,treepaths_list[treeindex])
        instructions_list.append(instructions_listelem)
        pass
        
    check_instruction_conflict(instructions_list)
        

    nsmap=dict(tree_orig.nsmap)
    # nsmap.update(tree_a.nsmap)
    for treeindex in range(len(treelist)):
        nsmap.update(treelist[treeindex].nsmap)
        pass

    # NOTE: If we wanted we could extract nsmaps from all children here
    # too. Probably not all that useful, though
    
    tree_new=etree.Element(tree_orig.tag,nsmap=nsmap)
    
    # create list for new element
    treeelems_new=[ copy.deepcopy(orig_el) for orig_el in treeelems_orig ]

    # clear out redundant tail text 
    for element in treeelems_new: 
        if hasattr(element,"tail"):
            element.tail=None
            pass
        pass

    treepaths_new=copy.deepcopy(treepaths_orig)

    #perform_instructions(tree_orig.tag,treeelems_new,treepaths_new,treeelems_b,treepaths_b,instructions_b,tag_index_paths_override)
    for treeindex in range(len(treelist)):
        perform_instructions(tree_orig.tag,treeelems_new,treepaths_new,treeelems_list[treeindex],treepaths_list[treeindex],instructions_list[treeindex],tag_index_paths_override,ignore_root_tag_name)
        pass
        
    reconcile(treeelems_orig,treepaths_orig,treeelems_new,treepaths_new,treeelems_list,treepaths_list,instructions_list,maxmergedepth,ignore_blank_text,tag_index_paths_override=tag_index_paths_override)

    # add treeelems_new to tree_new
    # import pdb;pdb.set_trace()

    tree_add_elements(tree_new,treeelems_new)
    return tree_new


                
