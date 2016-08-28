import sys
import imp
import os
sys.path.append('..')

from Services import S3TemplateService


def setup(server_data):
    def make_number(data):
        try:
            data = float(data)
        except ValueError:
            data = float(0)
        return data
    server_data['datatable'] = {}
    if 'lab_data' not in server_data:
        server_data['lab_data'] = server_data['lab_data_latest']
    cannabinoid_data = server_data['lab_data']['cannabinoids']['tests']
    thc_data = server_data['lab_data']['thc']['tests']
    if len(server_data['images']) == 0 and server_data['cover'] is None:
        image = 'https://st-orders.confidentcannabis.com/sequoia/assets/img/general/leaf-cover.png'
    else:
        if server_data['cover'] is None:
            image = 'https://st-orders.confidentcannabis.com/sequoia/assets/img/general/leaf-cover.png'
        else:
            image = 'https:' + server_data['cover']
    server_data['images'] = {}
    server_data['images']['0'] = image
    def get_concentration_total(data_list, display_value):
        concentration_total = 0.0
        for data in data_list:
            for analyte in data:
                if 'total' not in analyte:
                    concentration_total += make_number(data[analyte]['display'][display_value]['value'])
        return concentration_total

    total_concentration = get_concentration_total([cannabinoid_data, thc_data], '%')
    def combine_tests_for_viz(data_list, viz_type):
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

    def get_test_packages(server_data):
        test_names = []
        for i, package in enumerate(server_data):
            test_names.append(package['name'])
        return test_names

    combined_cannabinoids_dt = combine_tests_for_viz(
        [
            cannabinoid_data,
            thc_data
        ],
        'datatable')
    combined_cannabinoids_sl = combine_tests_for_viz(
        [
            cannabinoid_data,
            thc_data
        ],
        'sparkline')

    server_data['datatable'] = combined_cannabinoids_dt
    server_data['sparkline'] = combined_cannabinoids_sl
    credentials = {
        'aws_access_key_id': 'AKIAI5NYJC5SDJ3NKVIQ',
        'aws_secret_access_key': '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'
    }
    template_folder = server_data['lab']['abbreviation']
    print "Initializing S3TemplateService"
    if not os.path.exists('/tmp/work'):
        os.makedirs('/tmp/work')
    s3templates = S3TemplateService(credentials, 'pdfserver')
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
            'cc/coa/' + template_folder,
            'config.yaml',
            '/tmp/work/config.yaml'
        )
    except Exception as e:
        print str(e)
        return
    print "downloaded config"
    template_keys = get_test_packages(server_data['test_packages'])
    templates = s3templates.get_templates('/tmp/work/config.yaml', '/tmp/', template_keys)
    print "getting scripts"
    scripts = s3templates.get_scripts('/tmp/work/config.yaml')
    try:
        print "downloading templates"
        s3templates.download_templates('cc/coa/' + template_folder, templates)
        print "downloading scripts"
        s3templates.download_scripts('cc/coa/' + template_folder, scripts)
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
