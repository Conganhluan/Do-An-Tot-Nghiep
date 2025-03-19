from Helper import Helper

class Unmasker:

    def __init__(self, info_dict):
        '''
        info_dict example:
        {
            client_id_1: 
            {
                "is_alive": True/False,
                "secret_points": list[(x, y)],
                "public_secret": g^ps (mod q),
                "neighbor_list": list[neighbor_id]
            },
            client_id_2:
            ...
        }
        '''
        self.info_dict = info_dict

    