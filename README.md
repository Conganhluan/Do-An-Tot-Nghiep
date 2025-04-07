# Architecture

## Components

There are 3 components: Trusted party, Aggregator and Client(s)
- The Trusted party must be online first and wait for registration from the Aggregator and Client(s)
- The Aggregator must be online second and register with the Trusted party
- Then Client(s) can register with the Trusted party and get information about the Aggregator

## Threads

Each component has 3 threads: Commander, Controller and Listener
- Commander will be used for controlling/debugging/monitoring. It gets commands from stdin and acts as programmed. Here are some commands:
    - Shared commands: stop, restart, cls, *etc.*
    - Trusted party commands: public info, list client, init round *etc.*
    - Aggregator commands: register (used to re-register), pubic info, round info, *etc.*
    - Client commands: register (used to re-register), public info, client info, *etc.*
- Listener will get data/command from another components, then transfer requested data or set flag for the next action of Controller
- Controller will be the backbone of the components, it takes flags set by Commander and Listener and run the process

## Worker

- The main Worker is Manager, whose object will be shared among 3 Threads to keep the information synchronized.
- Another Worker is Helper, which will provide static methods for general process such as exponent_modulo, get_available_port, *etc.*
    - It also has static method `timing`, which can be used as method decorater to get the run time of another class methods
- Besides, there is Thread_Controller, which contains every async functions that Controller needs to run asynchronously

## ML models

- File `Aggregator/Thread/Worker/BaseModel.py` contains definitions of ML model, which can be used in this FL architecture
- To change the used model, please change the model type at `Aggregator/Main.py`, line 11
- The used model then can be transferred from the Aggregator > the Trusted party > Client(s) during registration processes

# Communication

0. Aggregator/Client aborts the process due to abnormal activities
```
Aggregator/Client   >>> ABORT <message>
3rd Trusted         >>> STOP <round_number> <message>
```

1. Aggregator registers itself with Trusted Party
```
Aggregator  >>> AGG_REGIS <aggregator_host> <aggregator_port> <aggregator RSA_public_key> <base_model_class>
3rd Trusted >>> <commiter>
Aggregator  >>> <base_model_commit>                                                         # commitment of the base model
3rd Trusted >>> SUCCESS
```

2. Client registers itself with Trusted Party
```
Client      >>> CLIENT <client_host> <client_port> <client RSA_public_key>                  # RSA_public_key: (e,d)
3rd Trusted >>> <aggregator_host> <aggregator_port> <aggregator RSA_public_key> <gs_mask> <commiter>
            >>> <base_model_class>
Client      >>> SUCCESS
```

3. Trusted Party gets DH public keys from chosen Clients
```
3rd Trusted >>> DH_PARAM <g> <q>                                                            # Diffile-Hellman: g^(secret_i)^(secret_j) mod q
Client      >>> <client_DH_public_key>
3rd Trusted >>> SUCCESS
```

4. Trusted Party sends round information to Clients
```
3rd Trusted >>> ROUND_INFO <round_number> <client_round_ID> <neighbor_num> 
            >>> <base_model_commit/previous_global_model_commit>
            In loop of <neighbor_num>:
                >>> <neighbor_round_ID> <neighbor_host> <neighbor_port> <neighbor_DH_public_key>
Client      >>> SUCCESS
```

5. Trusted Party sends round information to Aggregator
```
3rd Trusted >>> ROUND_INFO <round_number> <client_num> <q>
            In loop of <client_num>:
                >>> <client_round_ID> <client_host> <client_port> <client_DH_public_key> <client_RSA_public_key>
                >>> <client_neighbor_round_ID_1> <client_neighbor_round_ID_2> ... <client_neighbor_round_ID_n>
Aggregator  >>> SUCCESS
```

6. Aggregator sends global model to Clients
```
Aggregator  >>> GLOB_MODEL <r>                           # <r> is used in commitment
            >>> <global_model_parameters>
Client      >>> SUCCESS
```

7. Client sends secret points to its neighbors
```
Client      >>> POINTS <self_round_ID> <SS_point_X> <SS_point_Y> <PS_point_X> <PS_point_Y>                                          # (SS_point_X,SS_point_Y) is a point in polynomial F(x): x^n + ... + x^2 + x + <ss>
Other Client>>> SUCCESS
```

8. Client sends local model to Aggregator
```
Client      >>> LOCAL_MODEL <round_ID> <data_number> <data_num_signature> <parameters_signature>
            >>> <local_model_parameters> 
Aggregator  >>> SUCCESS <received_time> <signed_received_data>
        or  >>> OUT_OF_TIME <end_time>
```

9. Aggregator gets secrets points from Clients
```
Aggregator  >>> STATUS <neighbor_num>
            In loop of <neighbor_num>:
                >>> <neighbor_round_ID> <ON/OFF>
Client          >>> <SS_point_X/PS_point_X> <signature> <SS_point_Y/PS_point_Y> <signature>
Aggregator  >>> SUCCESS
```

10. Aggregator sends aggregated global model to Clients
```
Aggregator  >>> AGG_MODEL <ZKP_pubic_params> <r>                                                # <r> is used in commitment: commit = h^(data).k^r mod p
            >>> <global_parameters>
            >>> <parameters_commit>
            >>> <ZKP_proof>             
Client      >>> SUCCESS
```

11. Client sends round-end signal to Trusted Party
```
Client      >>> END <global_model_commit> <client_num>
            In loop of <client_num>:
                >>> <client_round_ID> <ON/OFF>
3rd Trusted >>> SUCCESS
```