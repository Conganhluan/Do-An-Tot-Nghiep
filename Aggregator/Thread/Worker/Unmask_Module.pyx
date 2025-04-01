ctypedef unsigned long long uint64
ctypedef long long int64
ctypedef unsigned long uint32
ctypedef long int32

def unmask_ss(const int64 [:] masked_parameters, int64 [:] unmasked_parameters, uint64 ss_mask):

    cdef Py_ssize_t param_num = masked_parameters.shape[0]
    assert masked_parameters.shape[0] == unmasked_parameters.shape[0]

    for idx in range(param_num):

         # Unmask it with ss_mask
        ss_mask ^= ss_mask << 3
        ss_mask ^= ss_mask >> 21
        ss_mask ^= ss_mask << 31
        unmasked_parameters[idx] = masked_parameters[idx] ^ ss_mask