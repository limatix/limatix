import sys
import os
import os.path
import re
import shutil
from setuptools import setup
from setuptools.command.install_lib import install_lib
from setuptools.command.install import install
import setuptools.command.bdist_egg
import distutils.spawn
import subprocess
import sys
import glob

exclude_directories = lambda files: [ file for file in files if not os.path.isdir(file) ]

#doc_files=exclude_directories(glob.glob("doc/*"))
#doc_pte_files=exclude_directories(glob.glob("doc/processtrak_example/*"))
#doc_pte_creston_files=exclude_directories(glob.glob("doc/processtrak_example/creston_jan2016/*"))
#xslt_files=glob.glob("xslt/*")
#root_files=["README.txt","INSTALL.txt"]
#limatix_widgets_glade_catalogs_package_files=["*.xml"]
limatix_widgets_package_files=["*.glade","glade_catalogs/*"]
limatix_checklist_steps_package_files=["*.glade"]
limatix_package_files=[
    "pt_steps/*.py",
    "*.glade",
    "limatix_checklists/*",
    "limatix_conf/*",
    "limatix_plans/*",
    "limatix_xslt/*"
]

console_scripts=["datacollect2",
                 "dc_checklist",
                 "pt_checkprovenance",
                 "dc_chx2chf",
                 "dc_glade",
                 "dc_gui",
                 "dc_paramdb2",
                 "thermal2limatix",
                 "processtrak",
                 "dc_ricohphoto",
                 "dc_xlg2dpd",
                 "pt_cleanup",
                 "limatix-git"]
gui_scripts = []  # Could move graphical scrips into here to eliminate stdio window on Windows (where would error messages go?)

console_scripts_entrypoints = [ "%s = limatix.bin.%s:main" % (script,script.replace("-","_")) for script in console_scripts ]
gui_scripts_entrypoints = [ "%s = limatix.bin.%s:main" % (script,script.replace("-","_")) for script in gui_scripts ]

canonicalize_path_config_files=["limatix/canonicalize_path/canonical_paths.conf.example","limatix/canonicalize_path/tag_index_paths.conf.example"]
canonicalize_path_package_files=["canonical_paths.conf","tag_index_paths.conf"]

limatix_checklist_step_paths=glob.glob("limatix/steps/*.py")
limatix_checklist_step_names=[ os.path.splitext(os.path.split(path)[1])[0] for path in limatix_checklist_step_paths if not path.endswith("__init__.py")]
limatix_checklist_step_entrypoints = [ '%s = limatix.steps.%s' % (stepname,stepname) for stepname in limatix_checklist_step_names]

limatix_widget_paths=glob.glob("limatix/widgets/*.py")
limatix_widget_names=[ os.path.splitext(os.path.split(path)[1])[0] for path in limatix_widget_paths if not path.endswith("__init__.py")]
limatix_widget_entrypoints = [ '%s = limatix.widgets.%s' % (widgetname,widgetname) for widgetname in limatix_widget_names]
print("limatix_widget_entrypoints",limatix_widget_entrypoints)
#package_files=["canonical_paths.conf","tag_index_paths.conf"]

# NOTE ***: share files will be installed to prefix/share/limatix
# By default, prefix is /usr so share_files to be found in
# /usr/share/limatix






setup(name="limatix",
      description="Automated data collection",
      author="Stephen D. Holland",
      # url="http://limatix.org/dataguzzler",
      zip_safe=False,
      packages=["limatix",
                "limatix.steps",
                "limatix.bin",
                "limatix.widgets", 
                "limatix.canonicalize_path", 
                "limatix.dc_lxml_treesync"],
      # package_dir=# {"limatix.canonicalize_path": "limatix/canonicalize_path/canonicalize_path"},
    
      package_data={"limatix.canonicalize_path": canonicalize_path_package_files, 
                    "limatix.widgets": limatix_widgets_package_files,
                    "limatix.steps": limatix_checklist_steps_package_files,
                    "limatix": limatix_package_files},
      entry_points={
          "limatix.checklist_search_path": [ "limatix.checklist_search_path_entry=limatix:getchecklisturlpath"],
          "limatix.checklist.step": limatix_checklist_step_entrypoints,
          "limatix.widget": limatix_widget_entrypoints,
          "limatix.datacollect2.config_url_search_path": [ "limatix.share.conf = limatix:getconfigurlpath" ],
          "limatix.processtrak.step_url_search_path": [ "limatix.share.pt_steps = limatix:getptstepurlpath" ],
          "console_scripts": console_scripts_entrypoints,
          "gui_scripts": gui_scripts_entrypoints })








