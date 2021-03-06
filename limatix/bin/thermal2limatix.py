#! /usr/bin/env python

import sys
import os
import os.path

from lxml import etree



# *****!!!*** move_namespace_decls_to_root is no longer needed!
move_namespace_decls_to_root=r"""<?xml version="1.0" encoding="UTF-8"?>
<!-- XSLT stylesheet for moving all namespace declarations to root node
-->

<xsl:stylesheet version="1.0"
		xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
		>

		<!--		xmlns:dc="http://limatix.org/datacollect" -->
  <xsl:output method="xml" encoding="utf-8"/>


  <!-- Match anything prior to root node, e.g. processing instruction or comment -->
  <xsl:template match="text()|comment()|processing-instruction()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>

  <!-- Match root node, inserting namespace declarations -->
  <xsl:template match="/*"> 
     <xsl:element name="{name()}" namespace="{namespace-uri()}">
       <xsl:copy-of select="//namespace::*"/>
       <xsl:apply-templates select="@*|node()" mode="body"/>
     </xsl:element>
  </xsl:template>

  <!-- match anything within root node -->
  <xsl:template match="@*|node()" mode="body">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()" mode="body"/>
    </xsl:copy>
  </xsl:template>
</xsl:stylesheet>
"""
  


convert_namespaces=r"""<?xml version="1.0" encoding="UTF-8"?>
<!-- XSLT stylesheet for converting old-style
http://thermal.cnde.iastate.edu/ XML namespaces to
new-style http://limatix.org

... Note that it doesn't put all namespace declarations in the
root node on its output, so we have to run it through another
converter to put those back in. 

-->

<!-- NOTE: When adding namespace mappings, see also namespace_mapping Python variable above -->
<xsl:stylesheet version="1.0"
		xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
		xmlns:xlink="http://www.w3.org/1999/xlink"
		xmlns:html="http://www.w3.org/1999/xhtml"
                xmlns:exsl="http://exslt.org/common"

		xmlns:dcp="http://thermal.cnde.iastate.edu/datacollect/provenance"
		xmlns:lip="http://limatix.org/provenance"
		
		xmlns:odc="http://thermal.cnde.iastate.edu/datacollect"
		xmlns:dc="http://limatix.org/datacollect"
		
		xmlns:odcv="http://thermal.cnde.iastate.edu/dcvalue"
		xmlns:dcv="http://limatix.org/dcvalue"

                xmlns:ochx="http://thermal.cnde.iastate.edu/checklist"
                xmlns:chx="http://limatix.org/checklist"

                xmlns:oprx="http://thermal.cnde.iastate.edu/datacollect/processinginstructions"
                xmlns:prx="http://limatix.org/processtrak/processinginstructions"

                xmlns:osp="http://thermal.cnde.iastate.edu/spatial"
                xmlns:sp="http://limatix.org/spatial"


		xmlns:odbvar="http://thermal.cnde.iastate.edu/databrowse/variable"
		xmlns:dbvar="http://limatix.org/databrowse/variable"
		
		xmlns:odbdir="http://thermal.cnde.iastate.edu/databrowse/dir"
		xmlns:dbdir="http://limatix.org/databrowse/dir"
		>
                <!-- *** SEE XMLNS declarations above AND LIST OF 
                         OVERRIDES BELOW -->
  <xsl:output method="xml" encoding="utf-8"/>

  <xsl:variable name="overrides">
    <override name="http://thermal.cnde.iastate.edu/datacollect">http://limatix.org/datacollect</override> 
    <override name="http://thermal.cnde.iastate.edu/datacollect/provenance">http://limatix.org/provenance</override>

    <override name="http://thermal.cnde.iastate.edu/dcvalue">http://limatix.org/dcvalue</override>

    <override name="http://thermal.cnde.iastate.edu/checklist">http://limatix.org/checklist</override>

    <override name="http://thermal.cnde.iastate.edu/datacollect/processinginstructions">http://limatix.org/processtrak/processinginstructions</override>

    <override name="http://thermal.cnde.iastate.edu/spatial">http://limatix.org/spatial</override>


    <override name="http://thermal.cnde.iastate.edu/databrowse/variable">http://limatix.org/databrowse/variable</override>
		
    <override name="http://thermal.cnde.iastate.edu/databrowse/dir">http://limatix.org/databrowse/dir</override>

  </xsl:variable>  



  <!-- The variable $converted_namespaces contains all of the root-node
       namespace xmlns= nodes, with nsuri's (but not prefixes) converted -->
  <xsl:variable name="converted_namespaces">

    <xsl:for-each select="/*/namespace::*">
      <xsl:variable name="nsuri"><xsl:value-of select="string()"/></xsl:variable>
      <xsl:choose>
        <!-- with prefix, and no override -->
        <xsl:when test="string-length(local-name()) &gt; 0 and not(exsl:node-set($overrides)/override[@name=$nsuri])">
          <xsl:element name="{ local-name() }:dummy" namespace="{ string() }"/> 
        </xsl:when>
        <!-- with prefix, and with override -->
        <xsl:when test="string-length(local-name()) &gt; 0 and exsl:node-set($overrides)/override[@name=$nsuri]">
          <xsl:element name="{ local-name() }:dummy" namespace="{ exsl:node-set($overrides)/override[@name=$nsuri] }"/> 
        </xsl:when>
        <!-- without prefix, and no override -->
        <xsl:when test="string-length(local-name()) = 0 and not(exsl:node-set($overrides)/override[@name=$nsuri])">
          <xsl:element name="dummy" namespace="{ string() }"/> 
        </xsl:when>
        <!-- without prefix, and with override -->
        <xsl:otherwise>
          <xsl:element name="dummy" namespace="{ exsl:node-set($overrides)/override[@name=$nsuri] }"/> 
        </xsl:otherwise>
      </xsl:choose>
    </xsl:for-each>
    <xsl:if test="/*/namespace::*[string(.)='http://thermal.cnde.iastate.edu/datacollect']">
      <!-- <dummy xmlns:dcfoo="http://limatix.org/datacollect"/> -->
    </xsl:if>
    
  </xsl:variable>


  <xsl:template match="dcp:*">
    <xsl:element name="lip:{local-name()}" namespace="http://limatix.org/provenance">
      <xsl:copy-of select="exsl:node-set($converted_namespaces)/*/namespace::*"/>
      <xsl:apply-templates select="@*|*|text()|comment()|processing-instruction()"/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="@dcp:*">
    <xsl:attribute name="lip:{local-name()}" namespace="http://limatix.org/provenance">
      <xsl:value-of select="."/>
    </xsl:attribute>
  </xsl:template>


  <xsl:template match="odc:*">
    <xsl:element name="{name()}" namespace="http://limatix.org/datacollect">
      <xsl:copy-of select="exsl:node-set($converted_namespaces)/*/namespace::*"/>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:element>
  </xsl:template>
  <xsl:template match="@odc:*">
    <xsl:attribute name="dc:{local-name()}" namespace="http://limatix.org/datacollect">
      <xsl:value-of select="."/>
    </xsl:attribute>
  </xsl:template>


  <xsl:template match="odcv:*">
    <xsl:element name="{name()}" namespace="http://limatix.org/dcvalue">
      <xsl:copy-of select="exsl:node-set($converted_namespaces)/*/namespace::*"/>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:element>
  </xsl:template>
  <xsl:template match="@odcv:*" namespace="http://limatix.org/dcvalue">
    <xsl:attribute name="dcv:{local-name()}">
      <xsl:value-of select="."/>
    </xsl:attribute>
  </xsl:template>


  <xsl:template match="ochx:*">
    <xsl:element name="{name()}" namespace="http://limatix.org/checklist">
      <xsl:copy-of select="exsl:node-set($converted_namespaces)/*/namespace::*"/>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:element>
  </xsl:template>
  <xsl:template match="@ochx:*">
    <xsl:attribute name="chx:{local-name()}" namespace="http://limatix.org/checklist">
      <xsl:value-of select="."/>
    </xsl:attribute>
  </xsl:template>

  <xsl:template match="oprx:*">
    <xsl:element name="{name()}" namespace="http://limatix.org/processtrak/processinginstructions">
      <xsl:copy-of select="exsl:node-set($converted_namespaces)/*/namespace::*"/>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:element>
  </xsl:template>
  <xsl:template match="@oprx:*">
    <xsl:attribute name="prx:{local-name()}" namespace="http://limatix.org/processtrak/processinginstructions">
      <xsl:value-of select="."/>
    </xsl:attribute>
  </xsl:template>


  <xsl:template match="odbvar:*">
    <xsl:element name="{name()}" namespace="http://limatix.org/databrowse/variable">
      <xsl:copy-of select="exsl:node-set($converted_namespaces)/*/namespace::*"/>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:element>
  </xsl:template>
  <xsl:template match="@odbvar:*">
    <xsl:attribute name="dbvar:{local-name()}" namespace="http://limatix.org/databrowse/variable">
      <xsl:value-of select="."/>
    </xsl:attribute>
  </xsl:template>

  <xsl:template match="odbdir:*">
    <xsl:element name="{name()}" namespace="http://limatix.org/databrowse/dir">
      <xsl:copy-of select="exsl:node-set($converted_namespaces)/*/namespace::*"/>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:element>
  </xsl:template>
  <xsl:template match="@odbdir:*">
    <xsl:attribute name="dbdir:{local-name()}" namespace="http://limatix.org/databrowse/dir">
      <xsl:value-of select="."/>
    </xsl:attribute>
  </xsl:template>


 
  <xsl:template match="*" priority="-2">
    <xsl:element name="{name()}" namespace="{namespace-uri()}">
      <xsl:copy-of select="exsl:node-set($converted_namespaces)/*/namespace::*"/>
      <xsl:apply-templates select="@*|*|text()|comment()|processing-instruction()"/>
    </xsl:element>
  </xsl:template>
  
  <xsl:template match="@*" priority="-2">
    <xsl:attribute name="{name()}" namespace="{namespace-uri()}"><xsl:value-of select="."/></xsl:attribute>
  </xsl:template>

  <xsl:template match="comment()|processing-instruction()" priority="-2">
    <xsl:copy>
      <xsl:apply-templates select="@*|*|text()|comment()|processing-instruction()"/>
    </xsl:copy>
  </xsl:template>

</xsl:stylesheet>
"""


def usage():
    print("Usage: %s <InputXMLFile>\n\n       Renames input file with .thns extension, and replaces it with a \n       copy where the thermal.cnde.iastate.edu namespaces have been\n       converted to limatix.org namespaces.\n\nWARNING: May not be perfect in all cases. Does unwrap CDATA,\nfor example. DOUBLE-CHECK WITH DIFF!!!\n" % (sys.argv[0]))
    pass

def main(args=None):
    if args is None:
        args=sys.argv
        pass
    

    
    inputfile=None
    
    cnt=1
    
    while cnt < len(args):
        if args[cnt].startswith("-"):
            if args[cnt]=="-h" or args[cnt]=="--help":
                usage()
                sys.exit(0)
                pass
            else:
                raise NameError("Unknown switch %s" % (args[cnt]))
            pass
        else:
            if inputfile is not None:
                raise ValueError("Only one positional parameter permitted")
            inputfile=args[cnt]
            pass
        cnt+=1
        pass
    
    if inputfile is None:
        usage()
        sys.exit(1)
        
        pass
    
    inputfh=file(inputfile)
    inputetree=etree.parse(inputfh)
    inputfh.close()

    convert_namespaces_transform=etree.XSLT(etree.XML(convert_namespaces))
    #move_namespace_decls_to_root_transform=etree.XSLT(etree.XML(move_namespace_decls_to_root))


    namespaces_transformed=convert_namespaces_transform(inputetree)
    
    #print(etree.tostring(namespaces_transformed))
    
    result_tree=namespaces_transformed #move_namespace_decls_to_root_transform(namespaces_transformed)
    
    backupfile=inputfile+".thns"

    os.rename(inputfile,backupfile)
    
    outputfh=file(inputfile,"w")
    result_tree.write(outputfh,encoding='utf-8',xml_declaration=True)
    outputfh.close()
    
    pass
