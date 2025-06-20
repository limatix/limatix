import sys
import os
import re
import copy
import math
import string 
import numpy as np
import datetime
import collections
import numbers
import urllib
import posixpath
import base64
import traceback

from lxml import etree

treesync=None
try: 
    from .dc_lxml_treesync import dc_lxml_treesync as treesync
    pass
except ImportError:
    sys.stderr.write("dc_value: Warning: unable to import dc_lxml_treesync -- XML comparisons not supported\n")
    pass

try:
    from cStringIO import StringIO
    pass
except ImportError:
    from io import StringIO
    pass


#from .canonicalize_path import href_context
from . import canonicalize_path

from . import provenance as provenance
# from . import xmldoc

from . import units as units_module
from . import lm_units

try: 
    import builtins  # python3
    pass
except ImportError: 
    import __builtin__ as builtins # python2
    pass

if not hasattr(builtins,"basestring"):
    basestring=str  # python3
    pass

__pychecker__="no-argsused no-override"


DCV="{http://limatix.org/dcvalue}"

def get_current_manager():
    if units_module.manager is None:
        print("WARNING: Attempting to instantiate limatix.dc_value.numericunitsvalue\nor .complexunitsvalue without a unit module configured.\nAuto-configuring lm_units.\nAdd unit configuration e.g.:\nfrom limatix.units import configure_units\nconfigure_units(\"lm_units\")\n\n\nTraceback follows:\n",file = sys.stderr)
        tb = traceback.extract_stack()
        traceback.print_tb(tb,file=sys.stderr)
        units_module.configure_units("lm_units",configstring = "insert_basic_units")
        pass
    return units_module.manager

# *** IMPORTANT *** 
# Need to add distinction between strings and identifiers, and deal with escaping, etc. 
# Deal with unicode? 

def xmlstoredisplayfmt(xmldocu,element,formatstr):
    if formatstr is not None:
        xmldocu.setattr(element,"dcv:displayfmt",formatstr)
        pass
    else:
        if xmldocu.hasattr(element,"dcv:displayfmt"):
            xmldocu.remattr(element,"dcv:displayfmt")
            pass
        pass
    
    pass

def xmlextractdisplayfmt(xmldocu,element):
    displayfmt=None
    if xmldocu.hasattr(element,"dcv:displayfmt"):
        displayfmt=xmldocu.getattr(element,"dcv:displayfmt")
        pass
    return displayfmt


def xmlstorevalueclass(xmldocu,element,valueclass):
    if value is not None:
        xmldocu.setattr(element,"dcv:valueclass",valueclass.__name__[:-5])  # store class name without trailing "value"
        pass
    else:
        if xmldocu.hasattr(element,"dcv:valueclass"):
            xmldocu.remattr(element,"dcv:valueclass")
            pass
        pass
    
    pass

def xmlextractvalueclass(xmldocu,element):
    globalvars=globals()
    valueclass=None
    if xmldocu.hasattr(element,"dcv:valueclass"):
        valueclassname="%svalue" % (xmldocu.getattr(element,"dcv:valueclass"))
        if valueclassname in globalvars:
            # have a variable of correct name. Make sure it is a class
            # that derives from class value
            if globalvars[valueclassname].__class__ is type: # is a class (i.e. a type)
                if issubclass(globalvars[valueclassname],value): # is a subclass of dc_value.value
                    valueclass=globalvars[valueclassname]
                    pass
                pass
            pass
                    
        pass
    return valueclass


class MergeError(Exception):
    value=None
    def __init__(self,value):
        self.value=value
        pass
    def __str__(self):
        return "MergeError: "+repr(self.value)
    pass




# still need to implement XML output!

# value object and subclasses are all final!
# May not be modified after creation. 


# NOTE: The value classes here are shadowed by paramdb2.param
# So extra methods/any public members added here must also have pass-throughs added to paramdb2.param

class value(object): 
    final=False
    

    def isblank(self):
        return False
    
    def __str__(self) :
        pass

    def format(self,formatstr):
        return str(self)

    
    def __eq__(self,other) :
        pass

    def equiv(self,other):
        # equivalence operator -- like equality
        # but determines whether there is a distinction, 
        # not mathematical equality. 
        #
        # Main difference so far: 
        # NaN == Nan is False, 
        # but NaN.equiv(NaN) is True

        # default behavior: Same as __eq__, but
        # returns True if both are blank
        if self.isblank() and other.isblank():
            return True

        return self.__eq__(other)



    # Define ne as inverse of whatever __eq__ operator is defined
    def __ne__(self,other) :
        return not self.__eq__(other)
    
    def __setattr__(self,name,value):
        if not self.final:
            return object.__setattr__(self, name, value);
        raise AttributeError("Value object has been finalized")

    #@classmethod
    #def __equal_with_blank(cls,a,b):
    #    # private... used by merge
    #    if a.isblank() and b.isblank():
    #        return True
    #    elif a.isblank() and not b.isblank():
    #        return False
    #    elif not(a.isblank()) and b.isblank():
    #        return False
    #    else: 
    #        return a==b
    #    pass

    
    @classmethod
    def merge(cls,parent,descendentlist,contexthref=None):
        # merge: Used to merge multiple, possibly inconsistent, values
        # If parent is None, merge semantics are to overwrite blanks but 
        # otherwise error out
        # if parent is not None, merge semantics are to keep a single change
        # from that parent but to error out if there are multiple changes

        if parent is None: 
            value=None
            for descendent in descendentlist: 
                if not descendent.isblank():
                    if value is None: 
                        value=descendent
                        pass
                    elif value != descendent:  
                       # two values -- raise exception!
                        raise MergeError("Cannot merge values: %s and %s" % (str(value),str(descendent)))

                    pass
                pass
            # if we made it this far, either we have a unique value, or all are blank
            if value is None:  # all are blank
                return descendentlist[0]
            return value
        else : 
            # parent specified, merge in the change!

            # We are looking to identify two unique values:
            # 1: Parent
            # 2: Something else.... stored in newvalue
            newvalue=None

            for descendent in descendentlist:
                if not(parent.equiv(descendent)):
                    if newvalue is not None and not newvalue.equiv(descendent): 
                        # two new values -- raise exception!
                        raise MergeError("Cannot merge values: Orig=%s; descendents %s and %s" % (str(parent),str(newvalue),str(descendent)))
                    
                    newvalue=descendent
                    pass
                pass
            if newvalue is None: # no changes at all
                newvalue=parent
                pass
            return newvalue
        pass

    pass


class xmltreevalue(value):
    # This value class represents XML tree
    # NOTE: It is built on xmldoc, so it only handles the primary 
    # text node within an element. Weird mixed structures -- 
    # such as in xhtml -- are not supported. 
    # ... it does ignore whitespace text nodes, so it supports pretty-printing. 

    __xmldoc=None  # PRIVATE -- must use get_xmldoc() to get a copy!!!
    
    def __init__(self,xmldoc_element_or_string,defunits=None,nsmap=None,contexthref=None,force_abs_href=False):
        from . import xmldoc   # don't want this in the top-of module because it creates a circular reference

        #sys.stderr.write("xmltreevalue.__init__: contexthref=%s\n" % (str(contexthref)))
        #if str(contexthref)=="./":
        #    import pdb
        #    pdb.set_trace()
        #
        #if contexthref is None and xmldoc_element_or_string is not None:
        #    if isinstance(xmldoc_element_or_string,self.__class__) and self.__xmldoc is None:
        #        pass
        #    else: 
        #        import pdb
        #        pdb.set_trace()
        #        pass
        #    pass
        
        # contexthref is desired context of new document (also assumed context of source, if source has no context)
        if isinstance(xmldoc_element_or_string,self.__class__):
            self.__xmldoc=xmldoc_element_or_string.get_xmldoc(nsmap=nsmap,contexthref=contexthref,force_abs_href=force_abs_href)
            pass            
        elif isinstance(xmldoc_element_or_string,xmldoc.xmldoc):
            self.__xmldoc=xmldoc.xmldoc.inmemorycopy(xmldoc_element_or_string,nsmap=nsmap,contexthref=contexthref,force_abs_href=force_abs_href)
            pass
        elif isinstance(xmldoc_element_or_string,etree._ElementTree):
            self.__xmldoc=xmldoc.xmldoc.copy_from_element(None,xmldoc_element_or_string,nsmap=nsmap,contexthref=contexthref,force_abs_href=force_abs_href)
            pass
        elif isinstance(xmldoc_element_or_string,etree._Element):
            self.__xmldoc=xmldoc.xmldoc.copy_from_element(None,xmldoc_element_or_string,nsmap=nsmap,contexthref=contexthref,force_abs_href=force_abs_href)
            
            pass
        elif xmldoc_element_or_string is None or xmldoc_element_or_string=="":
            self.__xmldoc=None  # Blank!
            pass
        else :
            # treat as string... note we skip whitespace 
            # so pretty-printing is ignored
            self.__xmldoc=xmldoc.xmldoc.fromstring(xmldoc_element_or_string,nsmap=nsmap,contexthref=contexthref,force_abs_href=force_abs_href)
            pass

        #if contextdir is None or contextdir=="":
        #    import pdb as pythondb
        #    pythondb.set_trace()

        self.final=True
        pass

    def getcontexthref(self):
        if self.__xmldoc is None:
            return hrefvalue(None)
        return self.__xmldoc.getcontexthref()
    
    
    def isblank(self):
        # blank if __xmldoc is None or if there are no elements
        
        if self.__xmldoc is None:
            return True
        
        if len(self.__xmldoc.xpath("node()|@*"))==0:
            # No elements
            return True
        return False
    


    def get_xmldoc(self,nsmap=None,contexthref=None,force_abs_href=False):
        from . import xmldoc   # don't want this in the top-of module because it creates a circular reference

        if self.__xmldoc is None: 
            return None
            
        # Returns a copy, so it's OK to write to it (but it won't have
        # any effect on the dc_value)
        return xmldoc.xmldoc.inmemorycopy(self.__xmldoc,nsmap=nsmap,contexthref=contexthref,force_abs_href=force_abs_href)

    def __unicode__(self):
        if self.__xmldoc is None:
            return u""
        return self.__xmldoc.tostring()
        
    def __str__(self):
        if self.__xmldoc is None:
            return ""
        if sys.version_info[0] >= 3: # Python 3... get unicode string
            return self.__xmldoc.tostring()
        else: 
            # Python 2... get bytes... and to minimize bugs
            # encode as ascii
            return self.__xmldoc.tobytes(encoding=None)
        pass

    def __eq__(self,other):
        othervalue=xmltreevalue(other)
        
        if self.__xmldoc is None and othervalue.__xmldoc is None:
            return True
        elif self.__xmldoc is None or othervalue.__xmldoc is None:
            return False
        #import pdb as pythondb
        if self.__xmldoc.getcontexthref() != other.__xmldoc.getcontexthref():
            # See if there are xlink:href attributes to screw things up
            attrsself=self.__xmldoc.xpath("//*[xlink:href]",namespaces={"xlink":"http://www.w3.org/1999/xlink"})
            attrsother=other.__xmldoc.xpath("//*[xlink:href]",namespaces={"xlink":"http://www.w3.org/1999/xlink"})
            
            if len(attrsself) != len(attrsother):
                return False
            
            if len(attrsself) > 0:
            
                #pythondb.set_trace()
                raise ValueError("xmltreevalue: Cannot currently compare trees with different context URLs %s and %s" % (str(self.__xmldoc.getcontexthref()),str(other.__xmldoc.getcontexthref())))
            pass
            
        return treesync.treesmatch(self.__xmldoc.getroot(),othervalue.__xmldoc.getroot(),True)

    def xmlrepr(self,xmldocu,element,defunits=None,force_abs_href=False):
        # WARNING: Adds in all attributes of this xml structure to element, 
        # but only cleans out those in the dcvalue namespace, so it is 
        # possible to unintentionally merge. 
        # 
        # The best course of action is not to allow the tree root to have attributes. 
        # NOTE: Cannot update document's or element's nsmap in any effective way. 
        #       This will need to be handled some other way

        # assert(xml_attribute is None) # An xml tree cannot fit in an attribute
        from . import xmldoc   # don't want this in the top-of module because it creates a circular reference

        oldattrs=element.attrib.keys()
        for oldattr in oldattrs:
            if oldattr.startswith(DCV):
                del element.attrib[oldattr]
                pass
            pass
        
        # Remove children
        element.text=""
        for child in element.getchildren():
            element.remove(child)
            pass
        
        if self.__xmldoc is not None:

            # do context conversion if necessary
            sourcecontext=self.__xmldoc.getcontexthref()
            targetcontext=xmldocu.getcontexthref()

            # if self.__xmldoc.getroot().tag=="http://limatix.org/checklist}subchecklists":
            #     sys.stderr.write("xmltreevalue.xmlrepr: tag=%s; sourcecontext=%s; targetcontext=%s\n" % (self.__xmldoc.getroot().tag,sourcecontext.absurl(),targetcontext.absurl()))
            #     sys.stderr.write("xmltreevalue=%s\n" % (str(self)))
            #     pass
            
            if sourcecontext is None or targetcontext is None:
                assert(0)
                # import pdb as pythondb
                # pythondb.set_trace()
                # pass
            
            # if canonicalize_path.canonicalize_path(sourcecontext) != canonicalize_path.canonicalize_path(targetcontext):
            if sourcecontext != targetcontext: 
                # create copy, in desired context
                treecopy=xmldoc.xmldoc.inmemorycopy(self.__xmldoc,contexthref=targetcontext,force_abs_href=force_abs_href)
                ourroot=treecopy.getroot()
                pass
            else: 
                ourroot=self.__xmldoc.getroot()
                pass

            # Copy our children
            ourroot=self.__xmldoc.getroot()
            element.attrib.update(dict(ourroot.attrib)) # copy attributes
            element.text=ourroot.text # copy text 
            for child in ourroot.getchildren(): # copy children
                element.append(copy.deepcopy(child))
                pass
            pass

        if xmldocu is not None:
            xmlstorevalueclass(xmldocu,element,self.__class__)
            

            xmldocu.modified=True
            for child in element.iter():
                provenance.elementgenerated(xmldocu,child)
                pass
            
            
            
            pass

        pass

    @classmethod
    def fromxml(cls,xmldocu,element,tagnameoverride=None,nsmap=None,defunits=None,contextdir=None,force_abs_href=False,noprovenance=False):
        # Create from a parsed xml representation. 
        # if tagnameoverride is specified, it will override the tag name of element
        # contexthref is the context href you want internally stored
        # in the object for relative links


        # assert(xml_attribute is None)  # storing content in an attribute does not make sense for an xml tre

        if xmldocu is not None and not noprovenance:
            provenance.xmldocelementaccessed(xmldocu,element)
            pass

        if tagnameoverride is not None:
            newelement=etree.Element(tagnameoverride,attrib=element.attrib,nsmap=element.nsmap)

            # Copy children (attributes already initialized)
            newelement.text=element.text # copy text 
            for child in element.getchildren(): # copy children
                newelement.append(copy.deepcopy(child))
                pass
            
            element=newelement
            pass

        # contexthref probably not needed anymore.... uncomment this if it is 
        #if contexthref is not None or force_abs_href:
        #    # need to adjust context. 
        #    # first create object in original context, then
        #    # convert its context
        ##   obj=cls(element,nsmap=nsmap,contextdir=xmldocu.getcontexthref())
        #
        #    # convert context
        #    obj.__xmldoc.setcontexthref(contexthref,force_abs_href=force_abs_href)
        #    return obj

        # sys.stderr.write("xmltreevalue.fromxml(): contexthref=%s\n" % (str(xmldocu.getcontexthref())))
        
        return cls(element,nsmap=nsmap,contexthref=xmldocu.getcontexthref())
    
    @classmethod
    def merge(cls,parent,descendentlist,contexthref=None,maxmergedepth=np.inf,tag_index_paths_override=None):
        # merge: Used to merge multiple, possibly inconsistent, values
        # If parent is None, merge semantics are to overwrite blanks but 
        # otherwise error out
        # if parent is not None, merge semantics are to merge the XML trees, up to maxmergedepth
        
        if parent is None or parent.__xmldoc is None: 
            # blank overwriting semantics
            value=None
            for descendent in descendentlist: 
                if not descendent.isblank():
                    if contexthref is not None:
                        if descendent.__xmldoc.getcontexthref() != contexthref:
                            # context mismatch. Redefine descendent with
                            # desired context
                            descendent=xmltreevalue(descendent,contexthref=contexthref)
                            pass
                        pass
                    if value is None: 
                        value=descendent
                        pass
                    elif value != descendent:  
                       # two values -- raise exception!
                        raise ValueError("Cannot merge values: %s and %s" % (str(value),str(descendent)))

                    pass
                pass
            # if we made it this far, either we have a unique value, or all are blank
            if value is None:  # all are blank
                # find any that actually has an object
                for descendent in descendentlist:
                    if descendent.__xmldoc is not None:
                        #sys.stderr.write("Merging trees... returning nonblank... contexthref=%s\n" % (descendent.__xmldoc.getcontexthref().absurl()))
                        return descendent
                    pass
                #sys.stderr.write("Merging trees... returning blank fallthrough\n")
                return descendentlist[0]
            return value

        else: 
            #sys.stderr.write("xmltreev merge\n")
            #sys.stderr.write("parent=%s\n\n" % (str(parent)))
            #cnt=0
            #for descendent in descendentlist:
            #    sys.stderr.write("descendent[%d]=%s\n\n" % (cnt,str(descendent)))
            #    cnt+=1
            #    pass

            #import pdb as pythondb
            #if contextdir is None or isinstance(contextdir,etree._Element) or parent.__xmldoc.getcontextdir() is None:
            #    pythondb.set_trace()
            #try : 

            desiredcontext=contexthref  # canonicalize_path.canonicalize_path(contextdir)
            #parentcontext=canonicalize_path.canonicalize_path(parent.__xmldoc.getcontextdir())
            parentcontext=parent.__xmldoc.getcontexthref()
            if parentcontext != desiredcontext:
                # Create copy of parent in the proper context
                parent=xmltreevalue(parent,contexthref=contexthref)
                pass
            
            # Create copy of descendentlist, but in the proper context
            #descendent_in_context_list=[ descendent if canonicalize_path.canonicalize_path(descendent.__xmldoc.getcontextdir())==desiredcontext else xmltreevalue(descendent,contextdir=contextdir) for descendent in descendentlist if descendent.__xmldoc is not None ]
            descendent_in_context_list=[ descendent if descendent.__xmldoc.getcontexthref()==desiredcontext else xmltreevalue(descendent,contexthref=contexthref) for descendent in descendentlist if descendent.__xmldoc is not None ]
                
            newelem=treesync.treesync_multi(parent.__xmldoc.getroot(),[descendent.__xmldoc.getroot() for descendent in descendent_in_context_list if descendent.__xmldoc is not None ],maxmergedepth,ignore_blank_text=True,tag_index_paths_override=tag_index_paths_override,ignore_root_tag_name=True)
            #    pass
            #except: 
            #    pythondb.post_mortem()
            #    pass
            pass

        #sys.stderr.write("Merging trees... tag=%s parent contexthref=%s descendent contexthrefs=%s output contexthref=%s\n" % (newelem.tag,parent.__xmldoc.getcontexthref().absurl(),",".join([descendent.__xmldoc.getcontexthref().absurl() for descendent in descendentlist if descendent.__xmldoc is not None ]),contexthref.absurl()))

        # sys.stderr.write("xmltreevalue.merge(): contexthref=%s\n" % (str(contexthref)))

        return cls(newelem,contexthref=contexthref)
    pass


class stringvalue(value):
    str=None

    def __init__(self,string,defunits=None) :
        if string is None:
            string=""
            pass

        self.str=str(string);
        self.final=True
        pass
    
    def isblank(self):
        # print "isblank() %d" % (len(self.str))
        if len(self.str) == 0:
            return True
        else : 
            return False
        pass
    
    def __str__(self) :
        return self.str;

    def xmlrepr(self,xmldocu,element,defunits=None):
        # NOTE: if xml_attribute is provided, xmldocu must be also.

        #print "xmlrepr!" + self.str
        # clear out any old attributes in the dcvalue namespace
        oldattrs=element.attrib.keys()
        for oldattr in oldattrs:
            if oldattr.startswith(DCV):
                del element.attrib[oldattr]
                pass
            pass

        text=self.str

        #if is_file_in_dest:
        #    # paramdb text is referring to a file in dest
        #    # need to find canonical location, then 
        #    # a relative path to that location
        #
        #    canonpath=canonicalize_path.canonicalize_relpath(dest,self.str)
        #    text=canonicalize_path.rel_or_abs_path(os.path.split(xmldocu.filename)[0],canonpath)
        #    pass

        #if xml_attribute is None: 
        # set text
        element.text=text
        #else: 
        #xmldocu.setattr(element,xml_attribute,text)
        #    pass
            
        if xmldocu is not None:
            xmldocu.modified=True
            provenance.elementgenerated(xmldocu,element)
            pass

        pass

    def value(self):
        if self.str is None:
            return ""
        return self.str
    

    @classmethod
    def fromxml(cls,xmldocu,element,defunits=None,contextdir=None,noprovenance=False):
        # NOTE: to use xml_attribute you must provide xmldocu)
        if xmldocu is not None and not noprovenance:
            provenance.xmldocelementaccessed(xmldocu,element)
            pass

        text=element.text
        # if xml_attribute is not None:
        #    text=xmldocu.getattr(element,xml_attribute,"")
        
        #if is_file_in_dest:
        #    # canonicalized file we are referring to 
        #    canonname=canonicalize_path.canonicalize_relpath(os.path.split(xmldocu.filename)[0],text)
        #    filepart=os.path.split(canonname)[1]
        #    # canonicalized dest
        #    canondest=canonicalize_path.canonicalize_path(dest)
        #    
        #    # put dest and filepart together... does it match canonname?
        #    if os.path.join(canondest,filepart)==canonname:
        #        # if so we strip off the path completely
        #        text=filepart
        #        pass
        #    # otherwise as-is
        #    pass

        return cls(text)
    
    
    
    def __eq__(self,other) :
        # print "StringValue Eq called!"
        if other is None and self.str is None:
            return True
        if other is None:
            return False
        
        # print "stringcomp(%s,%s)" % (self.str,str(other))
        return self.str==str(other);
    
    pass




class hrefvalue(value):
    href_context=None  # canonicalize_path.href_context object
    
    def __init__(self,URL,contexthref=None,defunits=None):
        if hasattr(contexthref,"href_context"):
            contexthref=contexthref.href_context
            pass
        
            
        if hasattr(URL,"href_context"):
            # hrefvalue object
            self.href_context=canonicalize_path.href_context(URL.href_context,contexthref)
            pass
        else:
            self.href_context=canonicalize_path.href_context(URL,contexthref)
            pass
        
        self.final=True
        pass
    
    pass


    def isblank(self):
        return self.href_context.isblank()

    def ismem(self):
        return self.href_context.ismem()
    
    def ishttp(self):
        return self.href_context.ishttp()
    
    def isfile(self):
        return self.href_context.isfile()
        
    def isabs(self):
        fullurl=str(self.href_context)
        return fullurl.startswith('/') or ":" in fullurl

    def __str__(self):
        return str(self.href_context)

    def absurl(self):
        return self.href_context.absurl()

    def humanurl(self):
        return self.href_context.humanurl()

    def canonicalize(self):
        return self.href_context.canonicalize()

        
    def islocalfile(self):
        return self.href_context.islocalfile()

    def attempt_relative_url(self,new_context):
        if hasattr(new_context,"href_context"):
            return self.href_context.attempt_relative_url(new_context.href_context)
        else:
            return self.href_context.attempt_relative_url(new_context)

        pass



    def attempt_relative_href(self,new_context):
        if hasattr(new_context,"href_context"):
            return self.href_context.attempt_relative_href(new_context.href_context)
        else:
            return self.href_context.attempt_relative_href(new_context)
        
        pass

    def xmlrepr(self,xmldocu,element,defunits=None,force_abs_href=False):

        self.href_context.xmlrepr(xmldocu,element,force_abs_href=force_abs_href)

        provenance.elementgenerated(xmldocu,element)

        pass

    def has_fragment(self):
        return self.href_context.has_fragment()

    def getunquotedfragment(self):
        return self.href_context.getunquotedfragment()
    
    def getquotedfragment(self):
        return self.href_context.getquotedfragment()

    def gethumanfragment(self):
        return self.href_context.gethumanfragment()

    def get_bare_quoted_filename(self):
        return self.href_context.get_bare_quoted_filename()
    
    def get_bare_unquoted_filename(self):
        return self.href_context.get_bare_unquoted_filename()

    def is_directory(self):
        return self.href_context.is_directory()
    
    def getpath(self):
        return self.href_context.getpath()

    def fragless(self):
        return hrefvalue(self.href_context.fragless())
    

    def leafless(self):
        # hrefvalues can include path and file. When defining a context, you
        # often want to remove the file part. This routine copies a href and
        # removes the file part, (but leaves the trailing slash)
        return hrefvalue(self.href_context.leafless())

        
    #@classmethod
    #def from_rel_path(cls,contextdir,path): # was frompath()
    #    # Path is desired file
    #    # Always stores relative path unless contextdir is None
    #    # contextdir is context relative to which path should be stored
    #    # will store absolute path otherwise

    #    if contextdir is not None:
    #        path=canonicalize_path.relative_path_to(contextdir,path)
    #        pass
    #    else: 
    ##        path=canonicalize_path.canonicalize_path(path)
    #        pass
    #        
    #    # create and return the context
    #    return hrefvalue(None,contextdir=contextdir,path=path)

    #@classmethod
    #def from_rel_or_abs_path(cls,contextdir,path):
    #    # Path is desired file
    #    # Stores relative path or absolute path
        # according to whether path is relative or
        # absolute (unless contextdir is None, in which case
        # path is always absolute)
        # contextdir is context relative to which path should be stored
        # will store absolute path otherwise
#
        #if contextdir is not None and not(os.path.isabs(path)):
        #    path=canonicalize_path.relative_path_to(contextdir,path)
        #    pass
        #else: 
        #    path=canonicalize_path.canonicalize_path(path)
        #    pass
        #    
        ## create and return the context
        #return hrefvalue(None,contextdir=contextdir,path=path)


        

    @classmethod
    def fromxml(cls,xmldocu,element,defunits=None,contextdir=None,noprovenance=False):
        # NOTE: to use xml_attribute you must provide xmldocu)
        # contextdir is ignored and obsolete
        
        if xmldocu is not None and not noprovenance:
            provenance.xmldocelementaccessed(xmldocu,element)
            pass

        href_context=canonicalize_path.href_context.fromxml(xmldocu,element)

        
        val=hrefvalue(href_context)
        
        return val
    
    def __hash__(self):
        return self.href_context.__hash__()
    
    def __eq__(self,other) :
        if hasattr(other,"href_context"):
            other=other.href_context
            pass
        
        return self.href_context.__eq__(other)


    @classmethod
    def fromelement(cls,xmldocu,element,tag_index_paths_override=None):
        return cls(canonicalize_path.href_context.fromelement(xmldocu,element,tag_index_paths_override=tag_index_paths_override))
    
    
    def value(self):
        return self.href_context
    
    
    def evaluate_fragment(self,xmldocu,refelement=None,noprovenance=False):
        return self.href_context.evaluate_fragment(xmldocu,refelement=refelement,noprovenance=noprovenance)
    
    pass


class complexunitsvalue(value) :
    defunit=None #!!! private
    quantity=None #!!! private...either a pint quantity or a (float value, lm_units) tuple
    manager=None #the units module implementation for this object
    # neither val nor unit are permitted to be None. 
    # val may be NaN
    # unit may be unitless.
    
    @property
    def val(self):
        return self.manager.value_from_quantity(self.quantity)

    @property
    def unit(self):
        return self.manager.units_from_quantity(self.quantity)

    def __init__(self,val,units=None,defunits=None) :
        self.manager = get_current_manager()
        
        if isinstance(val,basestring):
            self.quantity = self.manager.parse(val, units, defunits,parse_complex=True)
            pass
        elif hasattr(val,"value"):
            self.quantity = self.manager.from_numericunitsvalue(val, units=units)
            pass
        else:
            self.quantity = self.manager.from_value(val, units=units)
            pass

        if defunits is not None:
            self.defunit=self.manager.parseunits(defunits)
            pass
        
        self.final=True
        pass    
        
    def __reduce__(self):
        # lm_units is complicated to pickle, so instead, let's just 
        # pass this value as its actual value string and recreate it
        # as a new value object on the other side
        arg1 = self.__class__
        arg2 = (self.format(),)
        return (arg1, arg2)

    def isblank(self): # we represent blank as NaN
        return self.isnan()

    def numvalue(self,units=None):
        return self.value(units)

    def value(self,units=None):
        if units is None:
            return self.val;
        return self.manager.value_in_units(self,units)

    def units(self):
        return self.manager.units(self)

    def valuedefunits(self):
        return self.value(self.defunit)

    def format(self,unit=None):
        if unit is  None:
            unit=self.defunit
            pass
        
        if unit is None:
            
            return self.manager.format(self)

            pass
        else:
            return self.manager.format(self.manager.convert_units_to(self,unit))
        pass

    def comsolstr(self):
        if self.quantity is None: 
            return ""
        elif len(str(self.unit))==0 :
            return repr(self.val)
        else :
            return "%s[%s]" % (repr(self.val),str(self.unit))
        pass
    
    def __str__(self) :
        return self.manager.format(self)
    
    @classmethod
    def fromxml(cls,xmldocu,element,defunits=None,contextdir=None,noprovenance=False):
        # NOTE: if xml_attribute is provided, xmldocu must be also.

        # Check if we have a units attribute
        if xmldocu is not None and not noprovenance:
            provenance.xmldocelementaccessed(xmldocu,element)
            pass
        
        #if xml_attribute is None:
        elementtext=element.text
        #    pass
        #else: 
        #    elementtext=xmldocu.getattr(element,xml_attribute,"")
        #    pass


        if DCV+"units" in element.attrib:
            return cls(elementtext,element.attrib[DCV+"units"],defunits=defunits)
        elif "units" in element.attrib:
            return cls(elementtext,element.attrib["units"],defunits=defunits)
        else :
            return cls(elementtext,defunits=defunits)
        pass


    def xmlrepr(self,xmldocu,element,defunits=None):
        # NOTE: if xml_attribute is provided, xmldocu must be also.

        # clear out any old attributes
        oldattrs=element.attrib.keys()
        for oldattr in oldattrs:
            if oldattr.startswith(DCV):
                del element.attrib[oldattr]
                pass
            pass

        defunit=self.defunit

        if defunits is not None:
            # default unit set: force this unit
            defunit=self.manager.parseunits(defunits)
            # print "defunits: %s defunit: %s self.val: %s self.unit: %s" % (str(defunits),str(defunit),str(self.val),str(self.unit))
            pass
        
        
        if defunit is not None:
            
            if not self.manager.isnan(self):
                converted=self.manager.convert_units_to(self,defunit)
                
                if self.val is not None:
                    elementtext=repr(converted.val)
                    element.attrib[DCV+"units"]=str(converted.unit)
                    pass
                pass
            else :
                elementtext="NaN"
                element.attrib[DCV+"units"]=str(defunits)
                
                pass
            
            pass
        else : 
            if self.val is not None: 
                elementtext=repr(self.val)
                pass
            else :
                elementtext="NaN"
                pass
            
            element.attrib[DCV+"units"]=str(self.unit)
            
            pass

        #if xml_attribute is None: 
        # set text
        element.text=elementtext
        #    pass
        #else: 
        #    xmldocu.setattr(element,xml_attribute,elementtext)
        #    pass
        
        if xmldocu is not None:
            xmldocu.modified=True
            provenance.elementgenerated(xmldocu,element)
            pass
        
        pass

    def simplifyunits(self):
        return self.manager.simplifyunits(self)

    def inunits(self,unit): # unit conversion, new numericunitsvalue object
        return self.manager.convert_units_to(unit)
    
    def __eq__(self,other) :
        return self.manager.equal(self, other)

    def equiv(self,other):
        # Like __eq__ but determines equivalence, 
        # not equality. e.g. NaN equivalent to NaN
        return self.manager.equiv(self,other)
        
    def __lt__(self, other):
        return self.manager.less_than(self, other)


    def __le__(self, other):
        return self.manager.less_than_equal(self, other)


    def __gt__(self, other):
        return self.manager.greater_than(self, other)


    def __ge__(self, other):
        return self.manager.greater_than_equal(self, other)


    def __abs__(self):
        return self.manager.absolute_value(self)


    def __round__(self):
        return self.manager.round(self)


    def __pow__(self,other,modulo=None):
        return self.manager.power(self, other, modulo=modulo)
    

    def __add__(self,other):
        return self.manager.add(self, other)


    def __sub__(self,other):
        return self.manager.subtract(self, other)
    

    def __mul__(self,other):
        return self.manager.multiply(self, other)
    

    def __div__(self,other):
        return self.manager.divide(self, other)


    def __truediv__(self,other):
        return self.manager.true_divide(self, other)


    def __floordiv__(self,other):
        return self.manager.floor_divide(self, other)

    pass
    
class numericunitsvalue(value) :
    defunit=None #!!! private
    quantity=None #!!! private...either a pint quantity or a (float value, lm_units) tuple
    manager=None #the units module implementation for this object

    # neither val nor unit are permitted to be None. 
    # val may be NaN
    # unit may be unitless.
    
    @property
    def val(self):
        return self.manager.value_from_quantity(self.quantity)

    @property
    def unit(self):
        return self.manager.units_from_quantity(self.quantity)

    def __init__(self,val,units=None,defunits=None) :
        # self.name=name;
        self.manager = get_current_manager()
        
        if isinstance(val,basestring):
            self.quantity = self.manager.parse(val, units, defunits)
            pass
        elif hasattr(val,"value"):
            self.quantity = self.manager.from_numericunitsvalue(val, units=units)
            pass
        else:
            self.quantity = self.manager.from_value(val, units=units)
            pass

        if defunits is not None:
            self.defunit=self.manager.parseunits(defunits)
            pass
        
        self.final=True
        pass

    def __reduce__(self):
        # lm_units is complicated to pickle, so instead, let's just 
        # pass this value as its actual value string and recreate it
        # as a new value object on the other side
        arg1 = self.__class__
        arg2 = (self.format(),)
        return (arg1, arg2)

    def isblank(self): # we represent blank as NaN
        return self.isnan()

    def numvalue(self,units=None):
        return self.value(units)
    
    def __float__(self):
        # allow cast to float
        return float(self.value())

    def value(self,units=None):
        if units is None:
            return self.val;
        return self.manager.value_in_units(self,units)
    

    def units(self):
        return self.manager.units(self)
    

    def valuedefunits(self):
        return self.value(self.defunit)

    def format(self,unit=None):
        if unit is  None:
            unit=self.defunit
            pass
        
        if unit is None:
            
            return self.manager.format(self)

            pass
        else:
            return self.manager.format(self.manager.convert_units_to(self,unit))
        pass
      

    def comsolstr(self):
        if self.quantity is None: 
            return ""
        elif len(str(self.unit))==0 :
            return repr(self.val)
        else :
            return "%s[%s]" % (repr(self.val),str(self.unit))
        pass
    
    def __str__(self) :
        return self.manager.format(self)
     
    
    @classmethod
    def fromxml(cls,xmldocu,element,defunits=None,contextdir=None,noprovenance=False):
        # NOTE: if xml_attribute is provided, xmldocu must be also.

        if xmldocu is not None and not noprovenance:
            provenance.xmldocelementaccessed(xmldocu,element)
            pass

        #if xml_attribute is None:
        elementtext=element.text
        #    pass
        #else: 
        #    elementtext=xmldocu.getattr(element,xml_attribute,"")
        #    pass

        # Check if we have a units attribute
        if DCV+"units" in element.attrib:
            return cls(elementtext,element.attrib[DCV+"units"],defunits=defunits)
        elif "units" in element.attrib:
            return cls(elementtext,element.attrib["units"],defunits=defunits)
        else :
            return cls(elementtext,defunits=defunits)
        pass


    def xmlrepr(self,xmldocu,element,defunits=None):
        # NOTE: if xml_attribute is provided, xmldocu must be also.

        # clear out any old attributes
        oldattrs=element.attrib.keys()
        for oldattr in oldattrs:
            if oldattr.startswith(DCV):
                del element.attrib[oldattr]
                pass
            pass

        defunit=self.defunit

        if defunits is not None:
            # default unit set: force this unit
            defunit=self.manager.parseunits(defunits)
            # print "defunits: %s defunit: %s self.val: %s self.unit: %s" % (str(defunits),str(defunit),str(self.val),str(self.unit))
            pass
        
        
        if defunit is not None:
            
            if not self.manager.isnan(self):
                converted=self.manager.convert_units_to(self,defunit)
                
                if self.val is not None:
                    elementtext=repr(converted.val)
                    element.attrib[DCV+"units"]=str(converted.unit)
                    pass
                pass
            else :
                elementtext="NaN"
                element.attrib[DCV+"units"]=str(defunits)
                
                pass
            
            pass
        else : 
            if self.val is not None: 
                elementtext=repr(self.val)
                pass
            else :
                elementtext="NaN"
                pass
            
            element.attrib[DCV+"units"]=str(self.unit)
            
            pass

        #if xml_attribute is None: 
        # set text
        element.text=elementtext
        #    pass
        #else: 
        #    xmldocu.setattr(element,xml_attribute,elementtext)
        #    pass
        
        if xmldocu is not None:
            xmldocu.modified=True
            provenance.elementgenerated(xmldocu,element)
            pass
        
        pass
    

    def simplifyunits(self):
        return self.manager.simplifyunits(self)

    def inunits(self,unit): # unit conversion, new numericunitsvalue object
        return self.manager.convert_units_to(unit)
       
    def __eq__(self,other) :
        return self.manager.equal(self, other)

    def equiv(self,other):
        # Like __eq__ but determines equivalence, 
        # not equality. e.g. NaN equivalent to NaN
        return self.manager.equiv(self,other)

    def __lt__(self, other):
        return self.manager.less_than(self, other)


    def __le__(self, other):
        return self.manager.less_than_equal(self, other)


    def __gt__(self, other):
        return self.manager.greater_than(self, other)


    def __ge__(self, other):
        return self.manager.greater_than_equal(self, other)


    def __abs__(self):
        return self.manager.absolute_value(self)


    def __round__(self):
        return self.manager.round(self)


    def __pow__(self,other,modulo=None):
        return self.manager.power(self, other, modulo=modulo)
    

    def __add__(self,other):
        return self.manager.add(self, other)


    def __sub__(self,other):
        return self.manager.subtract(self, other)
    

    def __mul__(self,other):
        return self.manager.multiply(self, other)
    

    def __div__(self,other):
        return self.manager.divide(self, other)


    def __truediv__(self,other):
        return self.manager.true_divide(self, other)


    def __floordiv__(self,other):
        return self.manager.floor_divide(self, other)

    pass


class integervalue(value) :
    val=None  #!!! private

    # val may be None
    
    def __reduce__(self):
        # lm_units is complicated to pickle, so instead, let's just 
        # pass this value as its actual value string and recreate it
        # as a new value object on the other side
        arg1 = self.__class__
        arg2 = (str(self.val),)
        return (arg1, arg2)
        
    def __init__(self,val,defunits=None) :
        # self.name=name;

        
        if isinstance(val,basestring):
            if val=="None" or val=="":
                self.val=None
                pass
            else : 
                self.val=int(val)                
                pass
            pass
        elif hasattr(val,"value"):
            # val is already a dc_value object
            self.val=val.value()
            pass
        elif val is None:
            self.val=None
            pass
        else :
            self.val=int(val);
            pass

        
        self.final=True
        pass


    def isblank(self): 
        return self.val is None

    def numvalue(self):
        return self.value();

    def value(self):
        return self.val;


    def format(self,formatstr=None):
        # NOTE: Will not operate correctly if val is None and formatstr is specified
        
        if formatstr is None:
            if self.val is None:
                return ""
            return str(self.val)
        

        # print "formatstr=%s" % (formatstr)
        # if you get a 
        # TypeError: not all arguments converted during string formatting
        # on this next line, then you probably forgot the % in the %f or %g
        # in your initialization of displayfmt in the .dcc file
        return (formatstr) % (self.val)

    def comsolstr(self):
        return str(self.val)
    
    def __str__(self) :
        if self.val is None:
            return ""

        return str(self.val)
    
    @classmethod
    def fromxml(cls,xmldocu,element,defunits=None,contextdir=None,noprovenance=False):
        # NOTE: if xml_attribute is provided, xmldocu must be also.
        if xmldocu is not None and not noprovenance:
            provenance.xmldocelementaccessed(xmldocu,element)
            pass

        #if xml_attribute is None:
        elementtext=element.text
        #pass
        #else: 
        #    elementtext=xmldocu.getattr(element,xml_attribute,"")
        #    pass

        return cls(elementtext)


    def xmlrepr(self,xmldocu,element,defunits=None):
        # clear out any old attributes
        oldattrs=element.attrib.keys()
        for oldattr in oldattrs:
            if oldattr.startswith(DCV):
                del element.attrib[oldattr]
                pass
            pass


        #if xml_attribute is None: 
        # set text
        element.text=str(self.val)
        #    pass
        #else: 
        #    xmldocu.setattr(element,xml_attribute,str(self.val))
        #    pass
            
            
        
        if xmldocu is not None:
            xmlstorevalueclass(xmldocu,element,self.__class__)

            xmldocu.modified=True
            provenance.elementgenerated(xmldocu,element)
            pass
            
        pass
    
    
    def __eq__(self,other) :
        if self.val is None:
            return False

        assert(not hasattr(other,"units")) # don't support comparison between integervalue and numericunitsvalue at this point
        # if we want to support that later we could build off the code in numericunitsvalue

        otherval=other.value()
        return self.val==otherval


    
    def __add__(self,other):
        assert(self.val is not None)
        assert(not hasattr(other,"units")) # don't support arithmetic between integervalue and numericunitsvalue at this point
        if isinstance(other,int):
           
            return integervalue(self.val + other);
        else :
            raise ValueError("Attempting to add something other than int (%s) to dcv.integervalue " % (other.__class__.__name__))
            
        pass

    def __sub__(self,other):
        assert(self.val is not None)
        assert(not hasattr(other,"units")) # don't support arithmetic between integervalue and numericunitsvalue at this point
        if isinstance(other,int):
           
            return integervalue(self.val - other);
        else :
            raise ValueError("Attempting to subtract something other than int (%s) to dcv.integervalue " % (other.__class__.__name__))
            
        pass
    
    def __mul__(self,other):
        assert(self.val is not None)
        assert(not hasattr(other,"units")) # don't support arithmetic between integervalue and numericunitsvalue at this point
        if isinstance(other,int):
           
            return integervalue(self.val * other);
        else :
            raise ValueError("Attempting to multiply something other than int (%s) to dcv.integervalue " % (other.__class__.__name__))
            
        pass
        
    
    def __div__(self,other):
        assert(self.val is not None)
        assert(not hasattr(other,"units")) # don't support arithmetic between integervalue and numericunitsvalue at this point
        if isinstance(other,int):
           
            return integervalue(self.val // other);
        else :
            raise ValueError("Attempting to divide something other than int (%s) to dcv.integervalue " % (other.__class__.__name__))
            
        pass

    def __truediv__(self,other):
        assert(self.val is not None)
        assert(not hasattr(other,"units")) # don't support arithmetic between integervalue and numericunitsvalue at this point
        if isinstance(other,int):
           
            return integervalue(self.val // other);
        else :
            raise ValueError("Attempting to divide something other than int (%s) to dcv.integervalue " % (other.__class__.__name__))
            
        pass

    def __floordiv__(self,other):
        assert(self.val is not None)
        assert(not hasattr(other,"units")) # don't support arithmetic between integervalue and numericunitsvalue at this point
        if isinstance(other,int):
           
            return integervalue(self.val // other);
        else :
            raise ValueError("Attempting to divide something other than int (%s) to dcv.integervalue " % (other.__class__.__name__))
            
        pass

    pass







class booleanvalue(value) :
    val=None  #!!! private

    # val may be None
    
    def __reduce__(self):
        # lm_units is complicated to pickle, so instead, let's just 
        # pass this value as its actual value string and recreate it
        # as a new value object on the other side
        arg1 = self.__class__
        arg2 = (str(self.val),)
        return (arg1, arg2)
        
    def __init__(self,val,defunits=None) :
        # self.name=name;

        
        if isinstance(val,basestring):
            if val=="None" or val=="":
                self.val=None
                pass
            else :
                if val.lower()=="false" or val == "0":
                    self.val=False
                    pass
                elif val.lower()=="true" or val == "1":
                    self.val=True
                    pass
                else:
                    raise ValueError(f"Invalid string value for boolean: {val:s}")                
                pass
            pass
        elif hasattr(val,"value"):
            # val is already a dc_value object
            self.val=val.value()
            assert(isinstance(self.val,bool))
            pass
        elif val is None:
            self.val=None
            pass
        else :
            self.val=bool(val);
            pass

        
        self.final=True
        pass


    def isblank(self): 
        return self.val is None

    def numvalue(self):
        return self.value()*1.0;

    def value(self):
        return self.val;


    def format(self,formatstr=None):
        # NOTE: Will not operate correctly if val is None and formatstr is specified
        
        if formatstr is None:
            if self.val is None:
                return ""
            return str(self.val)
        

        # print "formatstr=%s" % (formatstr)
        # if you get a 
        # TypeError: not all arguments converted during string formatting
        # on this next line, then you probably forgot the % in the %f or %g
        # in your initialization of displayfmt in the .dcc file
        return (formatstr) % (self.val)

    def comsolstr(self):
        return str(self.val)
    
    def __str__(self) :
        if self.val is None:
            return ""

        return str(self.val)
    
    @classmethod
    def fromxml(cls,xmldocu,element,defunits=None,contextdir=None,noprovenance=False):
        # NOTE: if xml_attribute is provided, xmldocu must be also.
        if xmldocu is not None and not noprovenance:
            provenance.xmldocelementaccessed(xmldocu,element)
            pass

        #if xml_attribute is None:
        elementtext=element.text
        #pass
        #else: 
        #    elementtext=xmldocu.getattr(element,xml_attribute,"")
        #    pass

        return cls(elementtext)


    def xmlrepr(self,xmldocu,element,defunits=None):
        # clear out any old attributes
        oldattrs=element.attrib.keys()
        for oldattr in oldattrs:
            if oldattr.startswith(DCV):
                del element.attrib[oldattr]
                pass
            pass


        #if xml_attribute is None: 
        # set text
        element.text=str(self.val)
        #    pass
        #else: 
        #    xmldocu.setattr(element,xml_attribute,str(self.val))
        #    pass
            
            
        
        if xmldocu is not None:
            xmlstorevalueclass(xmldocu,element,self.__class__)

            xmldocu.modified=True
            provenance.elementgenerated(xmldocu,element)
            pass
            
        pass
    
    
    def __eq__(self,other) :
        if self.val is None:
            return False

        assert(not hasattr(other,"units")) # don't support comparison between booleanvalue and numericunitsvalue at this point
        # if we want to support that later we could build off the code in numericunitsvalue
        

        otherval=other.value()
        return self.val==bool(otherval)


    
    def __add__(self,other):
        raise ValueError("Attempting to add a boolean")

    def __sub__(self,other):
        raise ValueError("Attempting to subtract a boolean")
    
    def __mul__(self,other):
        raise ValueError("Attempting to multiply a boolean")
        
    
    def __div__(self,other):
        raise ValueError("Attempting to divide a boolean")

    def __truediv__(self,other):
        raise ValueError("Attempting to divide a boolean")

    def __floordiv__(self,other):
        raise ValueError("Attempting to divide a boolean")

    pass






class heatingvalue(numericunitsvalue) :
    pixbuf=None;
    def __init__(self,val,units=None,pixbuf=None) :
        self.pixbuf=pixbuf;
        numericunitsvalue.__init__(self,val,units); # this call finalizes the structure, so it must be last!
        pass
    
    pass

    

class excitationparamsvalue(value) : 
    type=None;
    wfm=None  # not yet fully implemented
    f0=None;
    f1=None;
    t0=None;
    t1=None;
    t2=None;
    t3=None;


    def __init__(self,string,defunits=None):
        if isinstance(string,dict):  # if we were provided with a dictionary of type, f1, f2, etc.
            paramdict=string

            #print "paramdict:", paramdict

            for key in paramdict:
                setattr(self,key,paramdict[key])
                pass
            self.final=True
            return
        elif isinstance(string,excitationparamsvalue):  # if we were provided with this class already, just copy it
            self.type=string.type
            self.f0=string.f0
            self.f1=string.f1
            self.t0=string.t0
            self.t1=string.t1
            self.t2=string.t2
            self.t3=string.t3
            
            self.final=True
            return
        elif string is None:
            # blank
            self.type=None
            return 
        # otherwise string really should be a string. 

        # should provide string with initial GEN: removed
        sweepmatch=re.match(r"""SWEEP Arb ([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?) Hz ([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?) Hz ([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?) s ([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?) s ([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?) s ([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?) s""",string)
        if (sweepmatch is not None) :
            self.type="SWEEP"
            self.f0=float(sweepmatch.group(1));
            self.f1=float(sweepmatch.group(2));
            self.t0=float(sweepmatch.group(3));
            self.t1=float(sweepmatch.group(4));
            self.t2=float(sweepmatch.group(5));
            self.t3=float(sweepmatch.group(6));
            if self.f0==self.f1 :
                self.type="BURST";
                pass
            pass
        else :
            burstmatch=re.match(r"""BURST Arb ([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?) Hz ([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?) s ([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?) s ([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?) s ([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?) s""",string)
            if (burstmatch is not None) :
                self.type="BURST"
                self.f0=float(burstmatch.group(1));
                self.f1=self.f0;
                self.t0=float(burstmatch.group(2));
                self.t1=float(burstmatch.group(3));
                self.t2=float(burstmatch.group(4));
                self.t3=float(burstmatch.group(5));
                pass
            else : 
                self.type=None
                pass
            pass
        self.final=True

        pass

    def isblank(self):
        return self.type is None
    
    
    def __str__(self) :
        # BUG: Should use repr's here instead of %g
        if self.type=="SWEEP" or self.type=="sweep":            
            return "SWEEP Arb %.2f Hz %.2f Hz %.8g s %.8g s %.8g s %.8g s" % (self.f0,self.f1,self.t0,self.t1,self.t2,self.t3)
        elif self.type=="BURST" or self.type=="burst":
            return "BURST Arb %.2f Hz %.8g s %.8g s %.8g s %.8g s" % (self.f0,self.t0,self.t1,self.t2,self.t3)
        elif self.type is not None :
            raise TypeError("Excitation type (%s) other than SWEEP or BURST" % (self.type));
        
        else:
            return ""
        pass

    
    def __eq__(self,other) :
        return type(self) is type(other) and self.type==other.type and self.f0==other.f0 and self.f1==other.f1 and self.t0==other.t0 and self.t1==other.t1 and self.t2==other.t2 and self.t3==other.t3



    @classmethod
    def fromxml(cls,xmldocu,element,defunits=None,contextdir=None,noprovenance=False):
        # NOTE: if xml_attribute must be none because of the structure used.

        #assert(xml_attribute is None)
        
        vals={}
        if xmldocu is not None and not noprovenance:
            provenance.xmldocelementaccessed(xmldocu,element)
            pass

        vals["type"]=element.attrib[DCV+"exctype"]
        

        for subel in element:
            if (subel.tag != DCV+"f0" and 
                subel.tag != DCV+"f1" and
                subel.tag != DCV+"t0" and
                subel.tag != DCV+"t1" and
                subel.tag != DCV+"t2" and
                subel.tag != DCV+"t3"):
                raise ValueError("excitationparamsvalue found invalid tag: %s" % (subel.tag))
            tag=subel.tag.split(DCV)[1]
            if tag[0]=='f':
                defunits="Hz"
                pass
            else : 
                defunits="s"
                pass
            
            vals[tag]=numericunitsvalue(subel.text,units=subel.attrib[DCV+"units"],defunits=defunits).valuedefunits()
            pass
        
        return cls(vals)
    
    def xmlrepr(self,xmldocu,tag,defunits=None): # usually "excitation" tag
        
        # as this tag has subelements it cannot be stored in an xml attribute
        #assert(xml_attribute is None)

        # clear out any attributes in the dcvalue namespace
        oldattrs=tag.attrib.keys()
        for oldattr in oldattrs:
            if oldattr.startswith(DCV):
                del tag.attrib[oldattr]
                pass
            pass

        while len(tag) > 0: 
            # remove any old subelements
            tag.remove(tag[0])
            pass
        
        if self.type is not None:

            tag.attrib[DCV+"exctype"]=self.type.lower()
            
            f0el=etree.Element(DCV+"f0")
            f0el.text=str(self.f0)
            f0el.attrib[DCV+"units"]="Hz"
            tag.append(f0el)
            
            if self.type == "SWEEP":
                f1el=etree.Element(DCV+"f1")
                f1el.text=str(self.f1)
                f1el.attrib[DCV+"units"]="Hz"
                tag.append(f1el)
                pass
            
            t0el=etree.Element(DCV+"t0")
            t0el.text=str(self.t0)
            t0el.attrib[DCV+"units"]="s"
            tag.append(t0el)
            
            t1el=etree.Element(DCV+"t1")
            t1el.text=str(self.t1)
            t1el.attrib[DCV+"units"]="s"
            tag.append(t1el)
            
            t2el=etree.Element(DCV+"t2")
            t2el.text=str(self.t2)
            t2el.attrib[DCV+"units"]="s"
            tag.append(t2el)
            
            t3el=etree.Element(DCV+"t3")
            t3el.text=str(self.t3)
            t3el.attrib[DCV+"units"]="s"
            tag.append(t3el)
            pass
        else : # type is None 
            tag.attrib[DCV+"exctype"]="INVALID"
            pass

        if xmldocu is not None:
            xmlstorevalueclass(xmldocu,tag,self.__class__)

            xmldocu.modified=True
            provenance.elementgenerated(xmldocu,tag)
            pass

        return
    



    pass

class imagevalue(value):
    PILimage=None

    def __init__(self,PILimage,defunits=None):

        if isinstance(PILimage,basestring):
            assert(PILimage=="") # blank string
            # leave self.PILimage as None
            return

        if hasattr(PILimage,"PILimage"):
            # This is really an imagevalue()
            self.PILimage=copy.copy(PILimage.PILimage)
            self.final=True
            return
        if PILimage is not None:
            self.PILimage=copy.copy(PILimage)
            pass

        self.final=True
        pass

    def __str__(self):
        return str(self.PILimage)

    @classmethod
    def fromxml(cls,xmldocu,element,defunits=None,noprovenance=False):
        # read src=... attribute like an html <img src="data:image/png;base64,..."/>
        from PIL import Image  # Need Python Imaging Library
        
        if not xmldocu.hasattr(element,"src",noprovenance=noprovenance):
            return imagevalue(None) # blank
        
        srcvalue=xmldocu.getattr(element,"src",noprovenance=noprovenance)

        if srcvalue.startswith("data:image/png;base64,"):
            imagedata=base64.b64decode(srcvalue[22:])
            PILimage=Image.open(StringIO(imagedata))
            pass
        elif srcvalue.startswith("data:image/jpeg;base64,"):
            imagedata=base64.b64decode(srcvalue[23:])
            PILimage=Image.open(StringIO(imagedata))            
            pass
        else:
            raise ValueError("Element src not base-64-encoded image data (starts instead as %s" % (srcvalue[:20]))

        return imagevalue(PILimage)

    def value(self):
        return self.PILimage

    def isblank(self):
        return self.PILimage is None

    def xmlrepr(self,xmldocu,tag,defunits=None):
        # Always save as PNG (lossless)

        if self.PILimage is None: # blank
            if xmldocu.hasattr(tag,"src"):
                xmldocu.remattr(tag,"src")
                pass
            return
        
        PNGbuf=StringIO()
        self.PILimage.save(PNGbuf,format="PNG")
        xmldocu.setattr(tag,"src","data:image/png;base64,"+base64.b64encode(PNGbuf.getvalue()))
        xmlstorevalueclass(xmldocu,tag,self.__class__)
        pass

    @classmethod
    def merge(cls,parent,descendentlist,contexthref=None,maxmergedepth=np.inf,tag_index_paths_override=None):
        
        for cnt in range(1,len(descendentlist)):
            if descendentlist[0] != descendentlist[cnt]:
                raise MergeError("Unable to merge inconsistent images")
            pass
        
        return descendentlist[0]

    def __eq__(self,other):
        from PIL import ImageChops

        if self.PILimage is None and other.PILimage is None:
            return True

        if self.PILimage is None or other.PILimage is None:
            return False
        
        # from http://effbot.org/zone/pil-comparing-images.htm:
        # The quickest way to determine if two images have exactly
        # the same contents is to get the difference between the two
        # images, and then calculate the bounding box of the non-zero
        # regions in this image. If the images are identical, all
        # pixels in the difference image are zero, and the bounding
        # box function returns None.
        
        return ImageChops.difference(self.PILimage, other.PILimage).getbbox() is None
    
    pass

class photosvalue(value):
    photoset=None # actually a frozenset
    # ...  of hrefvalues

    def __init__(self,value,defunits=None):
        if isinstance(value,tuple) or isinstance(value,list) or isinstance(value,set):
            self.photoset=frozenset(copy.deepcopy(value))
            pass
        elif isinstance(value,photosvalue):
            self.photoset=copy.deepcopy(value.photoset)
            pass
        elif isinstance(value,frozenset):
            self.photoset=copy.deepcopy(value)
            pass
        else :
            self.photoset=frozenset([])
            
            if value is not None and len(value) != 0:
                raise ValueError("photosvalue from string not yet implemented")
            pass
        pass

    def __str__(self):
        return ";".join([ os.path.split(photohref.getpath())[-1] for photohref in self.photoset ])

    def copyandappend(self,newphotohref):
        tmp=set(self.photoset)
        tmp.add(newphotohref)
        return photosvalue(tmp)

    def isblank(self):
        return len(self.photoset)==0
    
    
    @classmethod
    def fromxml(cls,xmldocu,element,defunits=None,contextdir=None,noprovenance=False):
        # NOTE: Does not currently handle context directories in a meaningful way (ignores them; assumes everything ends up in dest)
        #assert(xml_attribute=="xlink:href")
        if xmldocu is not None and not noprovenance:
            provenance.xmldocelementaccessed(xmldocu,element)
            pass
        tmp=set([])
        for subel in element:
            if subel.tag != DCV+"photo":
                raise ValueError("Photosvalue found non-dcv:photo tag: %s" % (subel.tag))
            tmp.add(hrefvalue.fromxml(xmldocu,subel,noprovenance=noprovenance))
            
            pass
        
        return cls(tmp)
    
    def xmlrepr(self,xmldocu,tag,defunits=None):
        # as this tag has subelements it cannot be stored in an xml attribute
        #assert(xml_attribute=="xlink:href")

        # clear out any attributes in the dcvalue namespace
        oldattrs=tag.attrib.keys()
        for oldattr in oldattrs:
            if oldattr.startswith(DCV):
                del tag.attrib[oldattr]
                pass
            pass

        while len(tag) > 0: 
            # remove any old subelements
            tag.remove(tag[0])
            pass
        
        for photohref in self.photoset:
            newel=etree.Element(DCV+"photo")
            tag.append(newel)
            photohref.xmlrepr(xmldocu,newel)
            pass
        if xmldocu is not None:
            xmlstorevalueclass(xmldocu,tag,self.__class__)

            xmldocu.modified=True
            provenance.elementgenerated(xmldocu,tag)
            pass
            
        return

    @classmethod
    def merge(cls,parent,descendentlist,contexthref=None,maxmergedepth=np.inf,tag_index_paths_override=None):
        #import pdb as pd
        #pd.set_trace()
        added=set([])
        removed=set([])
        if parent is not None:
            parentset=frozenset(parent.photoset)
            pass
        else:
            parentset=frozenset([])
            pass
        
        # ... for all descendents...
        for descendent in descendentlist:
            # find all photos that were added in this descendent
            # and all those that were removed in this descendent
            #sys.stderr.write("parentset=%s; descendent=%s\n" % (str(parentset),str(descendent)))
            added.update(descendent.photoset.difference(parentset))
            removed.update(parentset.difference(descendent.photoset))
            pass

        # if a photo was both added and removed, that is an error
        if len(added.intersection(removed)) > 0:
            raise MergeError("Error in merge: Photos %s were added in one descendent and removed in another descendent" % (str(added.intersection(removed)))) 

        return cls(parentset.difference(removed).union(added))

    def __eq__(self,other):
        return self.photoset==other.photoset
    
    pass

class datesetvalue(value):
    # represents a set of dates, separated by semicolons
    dateset=None
    
    def __init__(self,param,defunits=None):
        self.dateset=set([])
        if isinstance(param,collections.abc.Set):
            self.dateset=set(param)
            pass
        elif isinstance(param,basestring):
            self.dateset=self.parsedates(param)
            pass
        elif isinstance(param,datetime.date):
            self.dateset=set([param])
            pass
        elif isinstance(param,datetime.datetime):
            self.dateset=set([param.date()])
            pass
        elif param is None:
            self.dateset=set([])
            pass
        elif isinstance(param,datesetvalue):
            self.dateset=set(param.dateset)
            pass
        else : 
            raise ValueError("Unknown parameter type: %s for value %s\n" % (param.__class__.__name__,str(param)))
        self.final=True
        pass

    def parsedates(self,datesstr):
        # interpret both semicolon-delimited and comma-delimited
        if ";" in datesstr: 
            dates=datesstr.split(";")
            pass
        elif "," in datesstr:
            dates=datesstr.split(",")
            pass
        else: 
            dates=[datesstr]
            pass
        
        datesstrip=[date.strip() for date in dates]

        datesparsed=set([self.parsedate(date) for date in datesstrip if len(date) > 0])
        # sys.stderr.write("dates=%s datesparsed=%s\n" % (str(dates),str(datesparsed)))
        return datesparsed


    def parsedate(self,datestr):
        # sys.stderr.write("datestr=%s\n" % (datestr))
        return datetime.datetime.strptime(datestr,"%Y-%m-%d").date()
                        

    def union(self,other):
        # sys.stderr.write("Union(%s,%s)\n" % (str(self.dateset),str(other.dateset)))
        newset=self.dateset.union(other.dateset)
        return datesetvalue(newset)

    def __str__(self):
        sorteddates=[str(dateentry) for dateentry in self.dateset]
        sorteddates.sort()
        # sys.stderr.write("dateset=%s\n" % (str(self.dateset)))
        # sys.stderr.write("sorteddates=%s\n" % (sorteddates))
        return ",".join(sorteddates)
        
    @classmethod
    def fromxml(cls,xmldocu,element,defunits=None,contextdir=None,noprovenance=False):
        # NOTE: if xml_attribute is provided, xmldocu must be also.

        #if xml_attribute is None:
        elementtext=element.text
        #    pass
        #else: 
        #    elementtext=xmldocu.getattr(element,xml_attribute,"")
        #    pass

        if xmldocu is not None and not noprovenance:
            provenance.xmldocelementaccessed(xmldocu,element)
            pass
        return cls(elementtext)
    
    def xmlrepr(self,xmldocu,element,defunits=None):
        #if xml_attribute is None: 
        # set text
        element.text=str(self)
        #pass
        #else: 
        #    xmldocu.setattr(element,xml_attribute,str(self))
        #    pass

        if xmldocu is not None:
            xmlstorevalueclass(xmldocu,element,self.__class__)

            xmldocu.modified=True
            provenance.elementgenerated(xmldocu,element)
            pass

        pass

    def isblank(self):
        return len(self.dateset) == 0


    def __eq__(self,other) :
        return self.dateset==other.dateset
        
    def __contains__(self,other):
        return self.dateset >= other.dateset
    pass

class accumulatingdatesetvalue(datesetvalue):
    # derived class of datesetvalue
    # which overrides merge so that merged dates
    # accumulate (union) together
    
    def __init__(self,*args,**kwargs):
        #sys.stderr.write("adsv: %s %s\n" % (str(args),str(kwargs)))
        super(accumulatingdatesetvalue,self).__init__(*args,**kwargs)
        pass
    
    @classmethod
    def merge(cls,parent,descendentlist,contexthref=None):
        # merge them together
        accum=set([])
        if parent is not None:
            accum=accum.union(parent.dateset)
            pass

        for descendent in descendentlist:
            accum=accum.union(descendent.dateset)
            pass
        return cls(accum)




class integersetvalue(value) :
    setval=None  #!!! private

    # val may be None
    
        
    def __init__(self,val,defunits=None) :
        # self.name=name;

        
        if isinstance(val,basestring):
            if val=="None" or val=="":
                self.setval=None
                pass
            else : 
                if ";" in val:
                    self.setval = set([int(valuecomponent) for valuecomponent in val.split(";")])
                    pass
                elif "," in val: 
                    self.setval = set([int(valuecomponent) for valuecomponent in val.split(",")])                    
                    pass
                else : 
                    self.setval=set([int(val)])
                    pass
                pass
                
            pass
        elif isinstance(val,collections.abc.Set):
            self.setval=set(val)
            pass
        elif isinstance(val,list):
            self.setval=set(val)
            pass
        elif hasattr(val,"value"):
            # val is already a dc_value object
            self.setval=set(copy.copy(val.value()))
            pass
        elif val is None:
            self.setval=None
            pass
        else :
            self.setval=set([int(val)]);
            pass

        
        self.final=True
        pass


    def isblank(self): 
        return self.setval is None or len(self.setval)==0

    def value(self):
        if self.setval is None:
            return set([])
        return copy.copy(self.setval);
        


    def __str__(self) :
        if self.setval is None: 
            return ""

        # print out in sorted order
        setlist=list(self.setval)
        setlist.sort()
        
        return ",".join([str(intv) for intv in setlist])  # convert each element to a string, then join them with semicolons

        
    
    @classmethod
    def fromxml(cls,xmldocu,element,defunits=None,contextdir=None,noprovenance=False):
        # NOTE: if xml_attribute is provided, xmldocu must be also.
        if xmldocu is not None and not noprovenance:
            provenance.xmldocelementaccessed(xmldocu,element)
            pass

        #if xml_attribute is None:
        elementtext=element.text
        #    pass
        #else: 
        #    elementtext=xmldocu.getattr(element,xml_attribute,"")
        #    pass

        return cls(elementtext)


    def xmlrepr(self,xmldocu,element,defunits=None):
        # clear out any old attributes
        oldattrs=element.attrib.keys()
        for oldattr in oldattrs:
            if oldattr.startswith(DCV):
                del element.attrib[oldattr]
                pass
            pass

            
        #if xml_attribute is None: 
        # set text
        element.text=str(self)
        #pass
        #else: 
        #    xmldocu.setattr(element,xml_attribute,str(self))
        #    pass
            
        
        if xmldocu is not None:
            xmlstorevalueclass(xmldocu,element,self.__class__)

            xmldocu.modified=True
            provenance.elementgenerated(xmldocu,element)
            pass
            
        pass
    
    
    def __eq__(self,other) :
        if self.setval is None:
            return False

        assert(not hasattr(other,"units")) # don't support comparison between integervalue and numericunitsvalue at this point
        # if we want to support that later we could build off the code in numericunitsvalue

        otherval=other.value()
        return self.setval==otherval


    def union(self,other):
        # sys.stderr.write("Union(%s,%s)\n" % (str(self.dateset),str(other.dateset)))
        newset=self.setval.union(other.setval)
        return integersetvalue(newset)

    def __contains__(self,other):
        if hasattr(other,"setval"): # integersetvalue
            return self.setval >= other.setval
        elif isinstance(other,numbers.Number): # raw number
            return other in self.setval
        elif hasattr(other,"value"): # integervalue
            return other.value() in self.value 
        else:
            raise ValueError("Cannot determine whether %s is a subset" % (str(other)))
        pass
    pass




class accumulatingintegersetvalue(integersetvalue):
    # !!! NOT CURRENTLY USED !!!
    # derived class of datesetvalue
    # which overrides merge so that merged dates
    # accumulate (union) together
    
    def __init__(self,*args,**kwargs):
        #sys.stderr.write("adsv: %s %s\n" % (str(args),str(kwargs)))
        super(accumulatingintegersetvalue,self).__init__(*args,**kwargs)
        pass
    
    @classmethod
    def merge(cls,parent,descendentlist,contexthref=None):
        # merge them together
        accum=set([])
        if parent is not None and parent.setval is not None:
            accum=accum.union(parent.setval)
            pass

        for descendent in descendentlist:
            if descendent.setval is not None:
                accum=accum.union(descendent.setval)
                pass
            pass
        return cls(accum)

    pass
# This class is for matrices that may be read/written from XML files
# it is not intended for particularly large matrices. 
class arrayvalue(value):
    array=None  # Numpy array
    
    def __init__(self,array,defunits=None):
        if isinstance(array,arrayvalue):
            self.array=copy.copy(array.array)
            pass
        else:
            self.array=copy.copy(array)
            pass
        pass
    
    def __str__(self):
        return str(self.array)

    def xmlrepr(self,xmldocu,element,defunits=None):
        oldattrs=element.attrib.keys()
        for oldattr in oldattrs:
            if oldattr.startswith(DCV):
                del element.attrib[oldattr]
                pass
            pass
        oldchildren=element.getchildren()
        for child in oldchildren:
            element.remove(child)
            pass
        
        element.attrib[DCV+"arraystorageorder"]='C'
        
        nrows_element=etree.Element(DCV+"arrayshape")
        nrows_element.text=" ".join([str(axislen) for axislen in self.array.shape])
        element.append(nrows_element)
        data_element=etree.Element(DCV+"arraydata")
        data_element.text=" ".join(["%15.15g" % (arrayval) for arrayval in self.array.ravel(order="C")])
        element.append(data_element)

        xmlstorevalueclass(xmldocu,element,self.__class__)
            
        xmldocu.modified=True
        provenance.elementgenerated(xmldocu,element)
        
        pass
    
    @classmethod
    def fromxml(cls,xmldocu,element,defunits=None,noprovenance=False):
        if xmldocu is not None and not noprovenance:
            provenance.xmldocelementaccessed(xmldocu,element)
            pass
        
        arraystorageorder=element.attrib[DCV+"arraystorageorder"]
        shapeel=element.find(DCV+"arrayshape")
        shape=[int(axislen) for axislen in shapeel.text.split()]
        
        data_element=element.find(DCV+"arraydata")
        data=[float(dataval) for dataval in data_element.text.split()]

        array=np.array(data,dtype='d').reshape(*shape)
        return cls(array)
    pass

    def isblank(self):
        if np.prod(self.array.shape)==0:
            return True
        return False
    
    def value(self):
        return copy.copy(self.array)

    def __eq__(self,other):
        if isinstance(other,arrayvalue):
            return self.array==other.array
        else:
            return self.array==other
        pass

    pass


    
    
