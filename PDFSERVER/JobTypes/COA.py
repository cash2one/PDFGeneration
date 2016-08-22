from Services import S3TemplateService


def setup(server_data):
    server_data['datatable'] = {}
    cannabinoid_data = server_data['sample_data']['lab_data']['cannabinoids']['tests']
    thc_data = server_data['sample_data']['lab_data']['thc']['tests']

    def combine_tests_for_viz(data_list, viz_type):
        combined_list = []
        for data in data_list:
            for analyte in data:
                if viz_type == 'datatable':
                    combined_list.append(
                        [
                            str(analyte),
                            float(data[analyte]['display']['%']['loq']),
                            float(data[analyte]['display']['%']['value']),
                            float(data[analyte]['display']['mg/g']['value'])
                        ]
                    )
                if viz_type == 'sparkline':
                    combined_list.append(
                        [
                            str(analyte),
                            float(data[analyte]['display']['mg/g']['value'])

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

    server_data['datatable']['all_cannabinoids'] = (
        combined_cannabinoids_dt + combined_cannabinoids_sl
    )
    credentials = {
        'aws_access_key_id': 'AKIAI5NYJC5SDJ3NKVIQ',
        'aws_secret_access_key': 'WlnKj/6T4/kx9juBY/GUWOwpmtz8RKp+S5KrjSJM'
    }
    template_folder = server_data['sample_data']['lab']['abbreviation']
    s3templates = S3TemplateService(credentials, 'pdfserver')
    s3templates.download_config(
        'cc/coa/' + template_folder,
        'config.yaml',
        '.'
    )
    template_keys = get_test_packages(server_data['sample_data']['test_packages'])
    templates = s3templates.get_templates('config.yaml', '', template_keys)
    s3templates.download_templates('', templates)
    response = {
        'templates': templates,
        'data': server_data
    }
    return response
