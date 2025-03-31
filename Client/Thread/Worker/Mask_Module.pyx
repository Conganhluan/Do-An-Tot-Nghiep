cimport numpy as cnp
cnp.import_array()

ctypedef unsigned long long uint64
ctypedef long long int64
ctypedef unsigned long uint32
ctypedef long int32

def get_masked(cnp.ndarray[uint32, ndim=1, mode="c", cast=True] parameters, int64 [:] masked_parameters, uint64 ss_mask, int64 ps_mask, uint32 gs_mask):
    
    cdef uint32 HIDDEN_MANTISSA = 8388608           # 1000 0000 0000 0000 0000 0000
    cdef uint32 MANTISSA_BITS = 8388607             # last 23 bits

    cdef uint32 exponent_value                      # Used later
    cdef int32 mantissa_value                       # Used later
    cdef int64 shifted_value                        # Used later
    cdef int64 gs_masked_param                      # Used later
    cdef int64 ps_masked_param                      # Used later

    cdef Py_ssize_t param_num = parameters.shape[0]
    assert parameters.shape[0] == masked_parameters.shape[0]

    for idx in range(param_num):
        
        # Get the value
        exponent_value = parameters[idx] << 1 >> 24
        if exponent_value <= 75:
            shifted_value = 0                                                                                                       # Out of scope => Smallest value
        if exponent_value >= 132:
            shifted_value = 36028797018963967 * (1 - <int32>(parameters[idx] >> 31 << 1))                                           # Out of scope => Biggest value
        else:
            mantissa_value = ((parameters[idx] & MANTISSA_BITS) + HIDDEN_MANTISSA) * (1 - <int32>(parameters[idx] >> 31 << 1))      # The only last 25 bits specify the real value
            
            if exponent_value >= 100:
                shifted_value = <int64>mantissa_value << (exponent_value - 100)
            else:
                shifted_value = <int64>mantissa_value >> (100 - exponent_value)

        # print(f"Shifted value: {shifted_value}")

        # Mask it with 7 bits gs_mask
        gs_mask ^= gs_mask << 4
        gs_mask ^= gs_mask >> 5
        gs_mask ^= gs_mask << 15
        gs_masked_param = shifted_value * (1 + (gs_mask >> 26))

        # print(f"GS masked: {gs_masked_param}")

        # Mask it with 63 bits ps_mask
        ps_masked_param = gs_masked_param + (ps_mask >> 1)

        # print(f"PS masked: {ps_masked_param}")

        # Mask it with ss_mask
        ss_mask ^= ss_mask << 3
        ss_mask ^= ss_mask >> 21
        ss_mask ^= ss_mask << 31
        masked_parameters[idx] = ps_masked_param ^ ss_mask

        # print(f"SS masked: {masked_parameters[idx]}")

def get_unmasked(int64 [:] masked_parameters, cnp.ndarray[uint32, ndim=1, mode="c", cast=True] unmasked_parameters, uint32 gs_mask):

    cdef uint32 HIDDEN_MANTISSA = 8388608           # 1000 0000 0000 0000 0000 0000
    cdef uint32 MANTISSA_BITS = 8388607             # last 23 bits

    cdef uint32 exponent_value                          # Used later
    cdef int64 sign_value                               # Used later
    cdef uint64 abs_value
    cdef int64 gs_unmasked_param                        # Used later

    cdef Py_ssize_t param_num = masked_parameters.shape[0]
    assert masked_parameters.shape[0] == unmasked_parameters.shape[0]

    for idx in range(param_num):

        # Unmask it with gs_mask
        gs_mask ^= gs_mask << 4
        gs_mask ^= gs_mask >> 5
        gs_mask ^= gs_mask << 15
        gs_unmasked_param = masked_parameters[idx] // (1 + (gs_mask >> 26))

        # print(f"GS unmasked: {gs_unmasked_param}")

        # Convert to float32
        
        sign_value = gs_unmasked_param >> 63                        # 0 when gs_unmasked_param is positive and -1 when negative
        abs_value = (gs_unmasked_param ^ sign_value) - sign_value

        exponent_value = 131
        for exponent_value in range(131, 99, -1):
            if (abs_value >> 55) == 1:
                break
            else:
                abs_value <<= 1
        unmasked_parameters[idx] = (sign_value << 31) + (exponent_value << 23) + (abs_value << 1 >> 33)