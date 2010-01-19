import xml.sax
import re
import os

import ckan.model as model
from ckan.lib import schema_gov

#xsd_filepath = os.path.join(config['here'], 'ckan/getdata/ons_hub.xsd')

class Data(object):
    def load_xml_into_db(self, xml_filepath):
        self._basic_setup()
        rev = self._new_revision()
        assert os.path.exists(xml_filepath), xml_filepath
#        assert os.path.exists(xsd_filepath)
        handler = OnsXmlHandler(self.load_item)
        parser = xml.sax.parse(xml_filepath, handler)
        self._commit_and_report()

    def load_item(self, item):
        assert isinstance(item, dict)
        self._item_count += 1
        if self._item_count % 100 == 0:
            self._commit_and_report()
            
        title, release = self._split_title(item['title'])
        munged_title = schema_gov.name_munge(title)
        pkg = model.Package.by_name(munged_title)
        if not pkg:
            pkg = model.Package(name=munged_title)
            model.Session.add(pkg)
            self._new_package_count += 1
            rev = self._new_revision()
            model.Session.flush()

            # Setup authz
            user = model.User.by_name(self._username)
            model.setup_default_user_roles(pkg, [user]) # does commit & remove
            rev = self._new_revision()
            pkg = model.Package.by_name(munged_title)

        pkg.title = title
        # Resources
        guid = item['guid']
        existing_resource = None
        if guid:
            for res in pkg.resources:
                if res.description:
                    for desc_bit in res.description.split('|'):
                        if desc_bit.strip() == guid:
                            existing_resource = res
                            break
        url = item.get('link', None)
        descriptors = []
        if release:
            descriptors.append(release)
        if item.get('guid', None):
            descriptors.append(item['guid'])
        description = ' | '.join(descriptors)
        if existing_resource:
            res = existing_resource
            res.download_url = url
            res.description = description
        else:
            pkg.add_resource(url, description=description)
        notes_list = []
        if item['description']:
            notes_list.append(item['description'])
        for column, name in [('hub:source-agency', 'Source agency'),
                             ('hub:designation', 'Designation'),
                             ('hub:language', 'Language'),
                             ('hub:altTitle', 'Alternative title'),
                       ]:
            if item[column]:
                notes_list.append('%s: %s' % (name, item[column]))
        pkg.notes = '\n\n'.join(notes_list)
        rev = self._new_revision()
        pkg.license = model.License.by_name(u'Non-OKD Compliant::Crown Copyright')

        extras = {'geographic_coverage':u'', 'external_reference':u'', 'temporal_granularity':u'', 'date_updated':u'', 'agency':u'', 'precision':u'', 'geographical_granularity':u'', 'temporal_coverage_from':u'', 'temporal_coverage_to':u'', 'national_statistic':u'', 'department':u'', 'update_frequency':u'', 'date_released':u'', 'categories':u''}
        date_released = u''
        if item['pubDate']:
            try:
                date_released = schema_gov.DateType.iso_to_db(item['pubDate'], '%a, %d %b %Y %H:%M:%S %Z')
            except TypeError, e:
                print 'Warning: Could not read format of publication (release) date: %r' % e.args
        extras['date_released'] = date_released
        extras['department'] = self._source_to_department(item['hub:source-agency'])
        extras['agency'] = item['hub:source-agency'] if not extras['department'] else u''
        extras['categories'] = item['hub:theme']
        geo_coverage_type = schema_gov.GeoCoverageType.get_instance()
        extras['geographic_coverage'] = geo_coverage_type.str_to_db(item['hub:coverage'])
        extras['national_statistic'] = 'yes' if item['hub:designation'] == 'National Statistics' or item['hub:designation'] == 'National Statistics' else 'no'
        extras['geographical_granularity'] = item['hub:geographic-breakdown']
        extras['external_reference'] = u'ONSHUB'
        for update_frequency_suggestion in schema_gov.update_frequency_suggestions:
            item_info = ('%s %s' % (item['title'], item['description'])).lower()
            if update_frequency_suggestion in item_info:
                extras['update_frequency'] = update_frequency_suggestion
            elif update_frequency_suggestion.endswith('ly'):
                if update_frequency_suggestion.rstrip('ly') in item_info:
                    extras['update_frequency'] = update_frequency_suggestion
        for key, value in extras.items():
            pkg.extras[key] = value

        tags = set()
        for keyword in item['hub:ipsv'].split(';') + \
                item['hub:keywords'].split(';') + \
                item['hub:nscl'].split(';'):
            tags.add(schema_gov.tag_munge(keyword))
        existing_tags = pkg.tags
        for pkgtag in pkg.package_tags:
            if pkgtag.tag.name not in tags:
                pkgtag.delete()
            elif pkgtag.tag.name in existing_tags:
                tags.remove(pkgtag.tag.name)
        if tags:
            rev = self._new_revision()
        for tag in tags:
            pkg.add_tag_by_name(unicode(tag))

        if extras['department']:
            pkg.author = extras['department']

        model.Session.flush()

    def _source_to_department(self, source):
        dept_given = schema_gov.expand_abbreviations(source)
        department = None
        if '(Northern Ireland)' in dept_given:
            department = u'Northern Ireland Executive'
        for dept in schema_gov.government_depts:
            if dept_given in dept or dept_given.replace('Service', 'Services') in dept or dept_given.replace('Dept', 'Department') in dept:
                department = unicode(dept)
                
        if department:
            assert department in schema_gov.government_depts, department
            return department
        else:
            if dept_given and dept_given not in ['Office for National Statistics', 'Health Protection Agency', 'Information Centre for Health and Social Care', 'General Register Office for Scotland', 'Northern Ireland Statistics and Research Agency', 'National Health Service in Scotland', 'National Treatment Agency', 'Police Service of Northern Ireland (PSNI)', 'Child Maintenance and Enforcement Commission', 'Health and Safety Executive']:
                print 'Warning: Double check this is not a gvt department source: %s' % dept_given
            return dept_given
        


    def _split_title(self, xml_title):
        if not hasattr(self, 'title_re'):
            self.title_re = re.compile(r'([^-]+)\s-\s(.*)')
        match = self.title_re.match(xml_title)
        if not match:
            'Warning: Could not split title: %s' % xml_title
            return (xml_title, None)
        return match.groups()

    def _commit_and_report(self):
        print 'Loaded %i lines with %i new packages' % (self._item_count, self._new_package_count)
        model.repo.commit_and_remove()
    
    def _basic_setup(self):
        self._item_count = 0
        self._new_package_count = 0

        # ensure there is a user hmg
        self._username = u'hmg'
        user = model.User.by_name(self._username)
        if not user:
            user = model.User(name=self._username)
            model.Session.add(user)
            
        # ensure there is a group ukgov
        self._groupname = u'ukgov'
        group = model.Group.by_name(self._groupname)
        if not group:
            group = model.Group(name=self._groupname)
            model.Session.add(group)

    def _new_revision(self):
        # Revision info
        rev = model.repo.new_revision()
        rev.author = u'auto-loader'
        rev.log_message = u'Load from ONS Hub feed'
        return rev

class OnsXmlHandler(xml.sax.handler.ContentHandler):
    def __init__(self, load_item_func):
        xml.sax.handler.ContentHandler.__init__(self)
        self._load_item_func = load_item_func
    
    def startDocument(self):
        self._level = 0
        self._item_dict = {}        
        
    def startElement(self, name, attrs):
        self._level += 1
        if self._level == 1:
            if name == 'rss':
                pass
            else:
                print 'Warning: Not expecting element %s at level %i' % (name, self._level)
        elif self._level == 2:
            if name == 'channel':
                pass
            else:
                print 'Warning: Not expecting element %s at level %i' % (name, self._level)
        elif self._level == 3:
            if name == 'item':
                assert not self._item_dict
            elif name in ('title', 'link', 'description', 'language', 'pubDate', 'atom:link'):
                pass
        elif self._level == 4:
            assert name in ('title', 'link', 'description', 'pubDate', 'guid',
                            'hub:source-agency', 'hub:theme', 'hub:coverage',
                            'hub:designation', 'hub:geographic-breakdown',
                            'hub:ipsv', 'hub:keywords', 'hub:altTitle',
                            'hub:language',
                            'hub:nscl'), name
            self._item_element = name
            self._item_data = u''

    def characters(self, chrs):
        if self._level == 4:
            self._item_data += chrs

    def endElement(self, name):
        if self._level == 3:
            if self._item_dict:
                self._load_item_func(self._item_dict)
            self._item_dict = {}
        elif self._level == 4:
            self._item_dict[self._item_element] = self._item_data
            self._item_element = self._item_data = None
        self._level -= 1
