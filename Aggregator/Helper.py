from scipy.interpolate import lagrange
from json import load

class Helper:
    
    @staticmethod
    def get_free_coefficient(point_list: list[tuple[int, int]]) -> int:
        """
        Regenerate the polynomial from the points
        ------
        Return the polynomial
        """
        X, Y = [], []
        for x, y in point_list:
            X.append(x)
            Y.append(y)
        return int(lagrange(X, Y).coefficients.round())
    
    @staticmethod
    def get_env_variable(name: str) -> int | str:
        return load(open("../.env", "r", encoding='UTF-8'))[name]