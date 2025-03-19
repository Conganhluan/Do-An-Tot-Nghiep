class Manager:

    def __init__(self, basic_info_dict: dict):
        '''
        info_dict example:
        {
            client_id_1: 
            {
                "public_secret": g^ps (mod q),
                "neighbor_list": list[neighbor_id]
            },
            client_id_2:
            ...
        }
        '''
        self.info_dict = basic_info_dict

    