import numpy as np
import json
from Crypto.Cipher import AES
from pysnark.runtime import snark, PrivVal
from pysnark.fixedpoint import LinCombFxp
import numpy as np
from numpy import array
from numpy import poly1d


clients = [0,1,2,3]
neighbors = [[1,2],[0,3],[0,3],[1,2]]
wlc_unmasked = [10,15,25,400]
wlc_masked = [-2542629693, 73278774, 701766781, 1767584596]
secret=[1,2,3,4]
ps = [8,9,15,20]
public = [256,512,32768,1048576]
q = 1625358237


# def aes_ctr_prg(seed: int, num_bytes: int = 8):
#     """
#     Pseudo random generator using AES-CTR.
#     ------
#     Input:
#       - seed: integer used to generate a pseudo-random number
#       - num_bytes: length of the output in bytes
#     Output:
#       - A pseudo-random integer of size `num_bytes`
#     """
#     # Chuyển seed thành khóa AES (dùng SHA-256 -> 16 byte)
#     key = hashlib.sha256(str(seed).encode()).digest()[:16]

#     # Nonce 96-bit (12 byte) từ SHA-256 seed
#     nonce = hashlib.sha256(str(seed).encode()).digest()[:12]

#     # Tạo AES-CTR với nonce
#     cipher = AES.new(key, AES.MODE_CTR, nonce=nonce)
#     random_bytes = cipher.encrypt(b'\x00' * num_bytes)

#     # Chuyển thành số nguyên
#     result = int.from_bytes(random_bytes, "big")

#     return result


# def genPointofCurve(order, coeff_limit, point_num = -1):

#   point_num = order+1 if point_num<=order else point_num

#   # Create coeffs
#   coeffs = np.random.randint(-coeff_limit, coeff_limit, order+1)
#   if coeffs[0] == 0:
#     coeffs[0] = 1

#   # Get points
#   X = np.random.choice(range(-point_num//2-1, point_num//2+1), point_num, False)
#   X = X.tolist()
#   Y = [np.sum(coeffs*([x]**np.array(range(order, -1, -1)))) for x in X]
#   Y = [item.item() for item in Y] #[np.int64(a)]
#   return (coeffs, X, Y)


# @snark
# def regen_Curve(x,w):
#   x = array([item.value for item in x]) #[{a}]
#   w = array([item.value for item in w])
#   M = len(x)
#   p = poly1d((0.0))
#   for j in range(M):
#       pt = poly1d((w[j]))
#       for k in range(M):
#           if k == j:
#               continue
#           fac = (x[j]-x[k])
#           pt = pt*poly1d(([1.0, -x[k]]))/fac
#       p = p + pt
#   rounded_coeff = np.round(p.coefficients).astype(int) #[np.int(a)]
#   rounded_poly = poly1d(rounded_coeff)
#   return rounded_coeff[-1].item() #intercept



# @snark
# def aggregate(data):
#   # data = get_json_data("info_client_0.json")
#   number_clients = len(data["ids"])
  
#   wgn = LinCombFxp(PrivVal(0)) 
#   for client_id, client_info in data["ids"].items():

#     if client_info["status"].value == 1:
#       wgn -= client_info["ss"].value
#       wgn += client_info["wlc_masked"].value

#     if client_info["status"].value == 0:
#       neighbor_ids = array([item.value for item in data["relationships"][client_id]])
#       for neighbor_id in neighbor_ids:
#         neighbor_info = data["ids"][str(neighbor_id)]
#         if neighbor_info["status"].value == 0:
#           wgn -= client_info["public"].value**neighbor_info["ps"].value%q
    
#   wgn /= number_clients
#   return wgn.val()








# ################################################### UNIT TEST ########################################################
# # Test Curve
# coef, x, y = genPointofCurve(5, coeff_limit=20)
# coef2= regen_Curve(x,y)
# print("x: ", x)
# print("y: ", y)
# print("Real coef: ", coef)
# print("Regen coef: ", coef2)

# # Test aggregate
# with open('info_client_0.json','r') as file:
#   data = json.load(file)
#   # print(data)
# print(aggregate(data))

# wlc_masked = []
# for client in clients:
#   w_masked = wlc_unmasked[client] 
#   for neighbor in neighbors[client]:
#     if clients[neighbor] < client:
#       w_masked += public[neighbor]**ps[client]%q
#     if clients[neighbor] > client:
#       w_masked -= public[neighbor]**ps[client]%q
#   wlc_masked.append(w_masked)
# print(wlc_masked)
# print((np.sum(wlc_masked)-wlc_masked[1])/4)   




"""
Co the chon duoc cai nao se public tu file json
"""
# def test(data):
#   client_id = data["ids"]["0"]
  
#   @snark
#   def name(id):
#     return id
#   return name(client_id)


# # Test aggregate
# with open('info_client_0.json','r') as file:
#   data = json.load(file)
#   # print(data)
#   test(data)