from scipy.interpolate import lagrange

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
    