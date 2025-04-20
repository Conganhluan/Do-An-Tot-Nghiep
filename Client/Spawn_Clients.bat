set /P num="Number of clients: "
FOR /L %%x IN (1,1,%num%) DO (
    START python Main.py
    TIMEOUT /T 2
)