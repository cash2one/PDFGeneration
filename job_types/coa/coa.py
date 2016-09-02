import sys
import imp
import os
sys.path.append('../..')

from pdfservices import S3TemplateService
from collections import OrderedDict
from operator import itemgetter

def make_number(data):
    try:
        data = float(data)
    except ValueError:
        data = float(0)
    return data


def get_concentration_total(data_list, display_value):
    concentration_total = 0.0
    for data in data_list:
        for analyte in data:
            if 'total' not in analyte:
                try:
                    concentration_total += make_number(data[analyte]['display'][display_value]['value'])
                except Exception as e:
                    print str(e)
                    print "get_concentration_total exception"
                    concentration_total = 0.0
                    continue
    return concentration_total


def combine_tests_for_viz(data_list, viz_type, total_concentration=None):
    combined_list = []
    for data in data_list:
        for analyte in data:
            if 'total' not in analyte:
                if viz_type == 'datatable':
                    combined_list.append(
                        [
                            str(analyte),
                            make_number(data[analyte]['display']['%']['loq']),
                            make_number(data[analyte]['display']['%']['value']),
                            make_number(data[analyte]['display']['mg/g']['value'])
                        ]
                    )
                if viz_type == 'sparkline':

                    combined_list.append(
                        [
                            str(analyte),
                            make_number(data[analyte]['display']['%']['value']),
                            make_number(total_concentration)
                        ]
                    )

    return combined_list

def high_to_low(tested_analytes):
    analytes_and_values = {}
    for test in tested_analytes:
        for analyte in test:
            analytes_and_values[str(analyte)] = make_number(test[analyte]['display']['%']['value'])
    sorted_analytes_and_values = OrderedDict(sorted(analytes_and_values.items(), key=itemgetter(1)))
    return sorted_analytes_and_values.items()



def get_test_packages(server_data):
    test_names = []
    for i, package in enumerate(server_data):
        if 'package_key' not in package:
            package['package_key'] = None
        test_names.append([package['package_key'], package['name']])
    return test_names

def numberize(ordered_tuples):
    ordered_and_numbered = {}
    for i, e in enumerate(ordered_tuples):
        ordered_and_numbered[str(i)] = {}
        ordered_and_numbered[str(i)] = {"name": e[0], "value": e[1]}
    return ordered_and_numbered


def setup(server_data):

    server_data['viz'] = {}
    viztypes = server_data['viz']
    viztypes['job_type'] = 'coa'
    if 'lab_data_latest' in server_data:
        server_data['lab_data'] = server_data['lab_data_latest']
    if len(server_data['images']) == 0 and server_data['cover'] is None:
        image = 'https://st-orders.confidentcannabis.com/sequoia/assets/img/general/leaf-cover.png'
    else:
        if server_data['cover'] is None:
            image = 'https://st-orders.confidentcannabis.com/sequoia/assets/img/general/leaf-cover.png'
        else:
            image = 'https:' + server_data['cover']
    server_data['images'] = {}
    server_data['images']['0'] = image
    server_data['cover'] = image
    qr_base = "https://chart.googleapis.com/chart?chs=150x150&cht=qr&chl="
    public_profile_base = 'https%3A%2F%2Forders.confidentcannabis.com%2Fadvancedherbal%2F%23!%2Freport%2Fpublic%2Fsample%2F'
    public_key = server_data['public_key']
    server_data['qr_code'] = qr_base + public_profile_base + public_key
    template_folder = server_data['lab']['abbreviation']
    test_categories = ['cannabinoids', 'terpenes', 'solvents', 'microbials', 'mycotoxins', 'pesticides', 'metals']

    for category in test_categories:
        try:
            if category == 'cannabinoids':
                cbd_data = server_data['lab_data']['cannabinoids']['tests']
                thc_data = server_data['lab_data']['thc']['tests']
                ordered = high_to_low([cbd_data, thc_data])
                print "ordered:"
                print ordered
                ordered_and_numbered = numberize(ordered)
                print "ordered_and_numbered:"
                print ordered_and_numbered
                server_data[category + '_ordered'] = {}
                server_data[category + '_ordered'] = ordered_and_numbered
                print "server_data[category + '_ordered']:"
                print server_data[category + '_ordered']
                cannabinoid_data = server_data['lab_data']['cannabinoids']['tests']
                print "cannabinoid_data"
                print cannabinoid_data
                total_cannabinoid_concentration = get_concentration_total([cannabinoid_data, thc_data], '%')
                print "total_cannabinoid_concentration"
                print total_cannabinoid_concentration
                combined_cannabinoids_dt = combine_tests_for_viz(
                    [
                        cannabinoid_data,
                        thc_data
                    ],
                    'datatable')
                print "combined cannabinoid dt"
                combined_cannabinoids_sl = combine_tests_for_viz(
                    [
                        cannabinoid_data,
                        thc_data
                    ],
                    'sparkline',
                    total_cannabinoid_concentration)
                print "combined cannabinoid sl"
                viztypes['datatable_cannabinoids'] = combined_cannabinoids_dt
                viztypes['sparkline_cannabinoids'] = combined_cannabinoids_sl
            elif category == 'microbials':
                category_data = server_data['lab_data'][category]['tests']
                report_units = server_data['lab_data'][category]['report_units']
                print "yay for category data"
                total_category_concentration = get_concentration_total([category_data], report_units)
                print "yay for total_category_concentration"
                category_dt = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    'datatable')
                print "yay for category dt"
                category_sl = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    'sparkline',
                    total_category_concentration
                )
                print "yay for category sl"
                viztypes['datatable_' + category] = category_dt
                viztypes['sparkline_' + category] = category_sl
            else:
                category_data = server_data['lab_data'][category]['tests']
                print "yay for category data"
                total_category_concentration = get_concentration_total([category_data], '%')
                print "yay for total_category_concentration"
                category_dt = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    'datatable')
                print "yay for category dt"
                category_sl = combine_tests_for_viz(
                    [
                        category_data
                    ],
                    'sparkline',
                    total_category_concentration
                )
                print "yay for category sl"
                viztypes['datatable_' + category] = category_dt
                viztypes['sparkline_' + category] = category_sl
        except Exception as e:
            print "made it to the coa exception"
            print str(e)
            continue

    server_data['viz'] = viztypes
    print "Initializing S3TemplateService"

    if not os.path.exists('/tmp/work'):
        os.makedirs('/tmp/work')
    s3templates = S3TemplateService(bucket='cc-pdfserver')

    print "S3TemplateService initialized"
    def lambda_handler(event, context):
        print "made it to the lambda handler"
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        if not key.endswith('/'):
            try:
                split_key = key.split('/')
                file_name = split_key[-1]
                s3templates.s3.meta.client.download_file(
                    bucket_name,
                    key,
                    '/tmp/work/config.yaml'
                )
            except Exception as e:
                print str(e)
        return (bucket_name, key)
    try:
        s3templates.download_config(
            os.path.join('coa', template_folder),
            'config.yaml',
            '/tmp/work/config.yaml'
        )
    except Exception as e:
        print str(e)
        return

    print "downloaded config"
    template_keys = get_test_packages(server_data['test_packages'])
    templates = s3templates.get_templates('/tmp/work/config.yaml', '/tmp/', template_keys)
    lab_logo = s3templates.get_logo('/tmp/work/config.yaml')
    server_data['lab_logo'] = lab_logo
    print "getting scripts"
    scripts = s3templates.get_scripts('/tmp/work/config.yaml')
    try:
        print "downloading templates"
        s3templates.download_templates(os.path.join('coa', template_folder), templates)
        print "downloading scripts"
        s3templates.download_scripts(os.path.join('coa', template_folder), scripts)
    except Exception as e:
        print str(e)
        print str(os.listdir('/tmp'))
        return

    data = server_data
    for script in scripts:
        job = imp.load_source(
            '',
            os.path.join('/tmp', 'work', script))
        data = job.run(data)
    response = {
        'templates': templates,
        'data': data
    }

    print "made it to the end of this section......................................."
    return response
