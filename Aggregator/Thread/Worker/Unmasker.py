from Thread.Worker.Helper import Helper

class Unmasker:

    @staticmethod
    def get_secret(point_list: list[tuple[int, int]]) -> int:
        secret = Helper.get_secret(point_list)
        secret_check = Helper.get_secret(point_list[1:])
        if not secret == secret_check:
            print("2 secret calculated are different, there is something wrong!")
            print("Point list: " + ', '.join([f"({x}, {y})" for x, y in point_list]))
            print(f"Secret: {secret}")
            print(f"Secret test: {secret_check}")
            return 0
        return secret

    @staticmethod
    def get_PRNG_ss(ss: int) -> int:
        return abs(Helper.PRNG(ss, 8))
    
    @staticmethod
    def get_PRNG_ps(client_ID: int, client_ps: int, q: int, neighbor_info: list[tuple[int, int]]) -> int:
        total = 0.0
        for neighbor_ID, neighbor_DH_public_key in neighbor_info:
            if neighbor_ID > client_ID:
                total += Helper.PRNG(Helper.exponent_modulo(neighbor_DH_public_key, client_ps, q), 7)
            elif neighbor_ID < client_ID:
                total -= Helper.PRNG(Helper.exponent_modulo(neighbor_DH_public_key, client_ps, q), 7)
            else:
                raise Exception("There is something wrong here!")
        return total