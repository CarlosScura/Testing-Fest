import socket, threading, time
from conexion import HOST, PORT

class client():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conectado = False
        self.nombre = None
    
    def conectar(self):
        try:
            # solicitamos conexion al servidor
            self.socket.connect((self.host, self.port))
            pedido = self.socket.recv(1024).decode()
            print(pedido)
            self.nombre = input()
            self.socket.send(self.nombre.encode())
            self.conectado = True
            print(f"Conectado al chat como {self.nombre}")
        except:
            raise SystemExit("No se pudo conectar al servidor.")
    
    def reconectar(self):
        intentos = 0
        while intentos < 3:
            print(f"Intentando reconectar... ({intentos + 1}/3)")
            try:
                # creamos un socket nuevo porque el anterior está cerrado
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.host, self.port))
                _ = self.socket.recv(1024).decode()
                self.socket.send(self.nombre.encode())
                self.conectado = True
                print("Reconectado!")
                return
            except:
                intentos += 1
                time.sleep(5)
        
        raise SystemExit("No se pudo reconectar al servidor.")

    # thread 1
    def escuchar(self):
        while self.conectado:
            try:
                mensaje = self.socket.recv(1024).decode()
                if mensaje:
                    print(mensaje)
                else:
                    # si el mensaje esta vacio o da error, el servidor cayó
                    self.conectado = False
                    self.reconectar()
            except:
                # Si el cliente pidio su desconexión entonces no intenta reconectarse
                if self.conectado:
                    self.conectado = False
                    self.reconectar()
    
    # thread 2
    def enviar(self):
        while self.conectado:
            try:
                mensaje = input()
                if mensaje == "/exit":
                    self.socket.send(mensaje.encode())
                    self.conectado = False
                    self.socket.close()
                else:
                    self.socket.send(mensaje.encode())
            except:
                self.reconectar()

    def iniciar(self):
        self.conectar()
        
        # creamos los dos threads
        thread_escucha = threading.Thread(target=self.escuchar)
        thread_envio = threading.Thread(target=self.enviar)
        
        # daemon=True hace que los threads se cierren cuando el programa principal termina
        thread_escucha.daemon = True
        thread_envio.daemon = True
        
        thread_escucha.start()
        thread_envio.start()
        
        # esperamos a que el thread de envio termine
        thread_envio.join()

if __name__ == "__main__":
    cliente = client(HOST, PORT)
    cliente.iniciar()