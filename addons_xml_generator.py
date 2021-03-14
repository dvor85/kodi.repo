# -*- coding: utf-8 -*-
# *
# *  Copyright (C) 2012-2013 Garrett Brown
# *  Copyright (C) 2010      j48antialias
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of

# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with XBMC; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# *  Based on code by j48antialias:
# *  https://anarchintosh-projects.googlecode.com/files/addons_xml_generator.py

from __future__ import absolute_import, division, unicode_literals

""" addons.xml generator """

import os
import sys
import zipfile
import six
import xml.etree.ElementTree as XML

PY2 = sys.version_info[0] == 2


def uni(s, from_encoding='utf8'):
    """
    Декодирует строку из кодировки encoding
    :path: строка для декодирования
    :from_encoding: Кодировка из которой декодировать.
    :return: unicode path
    """

    if isinstance(s, six.binary_type):
        return s.decode(from_encoding, 'ignore')
    return s


def str2(s, to_encoding='utf8'):
    """
    PY2 - Кодирует :s: в :to_encoding:
    """
    if PY2 and isinstance(s, unicode):
        return s.encode(to_encoding, 'ignore')
    return str(s)


class Generator:
    """
        Generates a new addons.xml file from each addons addon.xml file
        and a new addons.xml.md5 hash file. Must be run from the root of
        the checked-out repo. Only handles single depth folder structure.
    """

    def __init__(self):
        # generate files
        self.root_dir = os.path.dirname(__file__)
        self._generate_addons_file()
        self._generate_md5_file(os.path.join(self.root_dir, "addons.xml"))
        # notify user
        print("Finished updating addons xml and md5 files")

    def _get_actual_version(self, addon):
        a_files = [a for a in os.listdir(os.path.join(self.root_dir, addon)) if a.endswith('.zip')]
        version = ''
        a_addon = None
        for a_file in a_files:
            try:
                c_file = os.path.join(self.root_dir, addon, a_file)
                with zipfile.ZipFile(c_file, mode='r') as zip_addon:
                    with zip_addon.open(addon + '/addon.xml') as addon_xml:
                        a_root = XML.parse(addon_xml).getroot()
                        c_version = a_root.get('version')
                        c_addon = os.path.join(self.root_dir, addon, "{id}-{ver}.zip".format(id=a_root.get('id'), ver=c_version))

                if os.path.abspath(c_addon) != os.path.abspath(c_file):
                    if os.path.exists(c_addon):
                        os.unlink(c_addon)
                    os.rename(c_file, c_addon)

                self._generate_md5_file(c_addon)
                if c_version >= version:
                    version = c_version
                    a_addon = c_addon
            except Exception as e:
                print(e)
        return a_addon, version

    def _generate_addons_file(self):
        # addon list

        addons = os.listdir(self.root_dir)
        # final addons text
        addons_xml = str2("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n<addons>\n")
        # loop thru and add each addons addon.xml file
        for addon in addons:
            try:
                # skip any file or .svn folder or .git folder
                if (not os.path.isdir(os.path.join(self.root_dir, addon)) or addon == ".svn" or addon == ".git"):
                    continue

                a_addon, version = self._get_actual_version(addon)
                if not a_addon:
                    continue
                with zipfile.ZipFile(a_addon, mode='r') as zip_addon:
                    try:
                        zip_addon.extract(addon + '/addon.xml')
                        zip_addon.extract(addon + '/changelog.txt')
                    except Exception as e:
                        pass

                # new addon
                addon_xml = ""
                with open(os.path.join(self.root_dir, addon, 'addon.xml'), mode='r') as a_xml:
                    xml_lines = uni(a_xml.read()).splitlines()
                # loop thru cleaning each line
                for line in xml_lines:
                    # skip encoding format line
                    if (line.find("<?xml") >= 0):
                        continue
                    # add line
                    addon_xml += line.rstrip() + "\n"
                # we succeeded so add to our final addons.xml text
                print("Add {a}".format(a=addon))

                addons_xml += addon_xml.rstrip() + "\n\n"
            except Exception as e:
                # missing or poorly formatted addon.xml
                print(e)
        # clean and add closing tag
        addons_xml = addons_xml.strip() + "\n</addons>\n"
        # save file
        self._save_file(addons_xml, os.path.join(self.root_dir, "addons.xml"))

    def _generate_md5_file(self, _file):
        # create a new md5 hash
        try:
            import md5
            m = md5.new(open(_file, "rb").read()).hexdigest()
        except ImportError:
            import hashlib
            m = hashlib.md5(open(_file, "rb").read()).hexdigest()

        # save file
        try:
            self._save_file(str2(m), "{f}.md5".format(f=_file))
        except Exception as e:
            # oops
            print("An error occurred creating addons.xml.md5 file!\n%s" % e)

    def _save_file(self, data, _file):
        try:
            # write data to the file (use b for Python 3)
            with open(_file, "w") as fp:
                fp.write(data)
            pass
        except Exception as e:
            # oops
            print("An error occurred saving %s file!\n%s" % (_file, e))


if (__name__ == "__main__"):
    # start
    Generator()
