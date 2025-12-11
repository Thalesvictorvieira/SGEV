import customtkinter as ctk
import sqlite3
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import io

# --- Configurações Iniciais ---
ctk.set_appearance_mode("System")  # Padrão do sistema operacional
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

         #1. Configuração da Janela Principa
        self.title("Sistema de Armazém de Bebidas")
        self.geometry("1000x700")

        # Configurar grid: Linha 0 (Navegação), Linha 1 (Conteúdo)
        self.grid_rowconfigure(1, weight=1) 
        self.grid_columnconfigure(0, weight=1)

        # --- 2. Configuração do Banco de Dados ---
        self.conn = sqlite3.connect('armazem_bebidas.db')
        self.cursor = self.conn.cursor()
        self.setup_database()

        # --- 3. Container de Conteúdo (onde as abas aparecem) ---
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.content_frame.grid_rowconfigure(0, weight=1)
        # CORREÇÃO: Usar .grid_columnconfigure no widget correto (self.content_frame)
        self.content_frame.grid_columnconfigure(0, weight=1) 

        # --- 4. Inicialização dos Frames (Telas) ---
        self.login_frame = LoginFrame(self.content_frame, self.show_main_interface)
        self.cadastro_frame = CadastroFrame(self.content_frame, self.cadastrar_produto)
        # Passa o método de consulta para o frame de visualização
        self.view_products_frame = ViewProductsFrame(self.content_frame, self.get_all_products)

        # --- 5. Barra de Navegação (Segmented Button) ---
        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0)
        # Ocupa a linha 0 da janela principal (self)
        self.navigation_frame.grid(row=0, column=0, sticky="ew")
        self.navigation_frame.grid_columnconfigure(0, weight=1) 

        self.segmented_button = ctk.CTkSegmentedButton(self.navigation_frame,
                                                      values=["Cadastrar Produto", "Ver Produtos"],
                                                      command=self.change_tab)
        self.segmented_button.grid(row=0, column=0, pady=10, padx=20)
        self.segmented_button.set("Cadastrar Produto") 

        # Esconder navegação e começar no login
        self.navigation_frame.grid_forget()
        self.show_login()

    def setup_database(self):
        # Tabela para produtos com campo 'foto BLOB'
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY,
                nome TEXT NOT NULL,
                tipo TEXT NOT NULL,
                quantidade INTEGER NOT NULL,
                preco REAL NOT NULL,
                foto BLOB
            )
        ''')
        self.conn.commit()

    def show_login(self):
        self.cadastro_frame.grid_forget()
        self.view_products_frame.grid_forget()
        self.navigation_frame.grid_forget() 
        self.login_frame.grid(row=0, column=0, sticky="nsew")

    def show_main_interface(self):
        # Chamado após o login bem-sucedido
        self.login_frame.grid_forget()
        self.navigation_frame.grid(row=0, column=0, sticky="ew") 
        self.change_tab("Cadastrar Produto") # Ir para a aba de cadastro

    def change_tab(self, value):
        if value == "Cadastrar Produto":
            self.view_products_frame.grid_forget()
            self.cadastro_frame.grid(row=0, column=0, sticky="nsew")
        elif value == "Ver Produtos":
            self.cadastro_frame.grid_forget()
            self.view_products_frame.grid(row=0, column=0, sticky="nsew")
            # Recarrega os produtos toda vez que a aba de visualização é aberta
            self.view_products_frame.load_products() 

    def cadastrar_produto(self, nome, tipo, quantidade, preco, foto_bytes):
        # CORREÇÃO: Robustez na validação e tratamento de erros do BD
        try:
            # 1. Validação e Conversão
            quantidade = int(quantidade)
            preco = float(preco)
            
            if quantidade < 0 or preco < 0:
                 messagebox.showerror("Erro", "Quantidade e Preço devem ser valores positivos.")
                 return
            if not nome or not tipo:
                messagebox.showerror("Erro", "Nome e Tipo do produto são obrigatórios.")
                return

            # 2. Tratamento do BLOB (Foto)
            # Garante que o valor inserido é None (NULL no SQLite) se nenhuma foto for selecionada
            foto_data = foto_bytes if foto_bytes else None 
            
            # 3. Execução da Inserção
            self.cursor.execute('''
                INSERT INTO produtos (nome, tipo, quantidade, preco, foto) VALUES (?, ?, ?, ?, ?)
            ''', (nome, tipo, quantidade, preco, foto_data))
            
            self.conn.commit()
            messagebox.showinfo("Sucesso", f"Produto '{nome}' cadastrado com sucesso!")
            
        except ValueError:
            messagebox.showerror("Erro de Entrada", "Quantidade deve ser um número inteiro e Preço um número real (Ex: 12.50).")
        
        except sqlite3.Error as e:
            messagebox.showerror("Erro no BD", f"Ocorreu um erro de banco de dados ao cadastrar. Detalhe: {e}")

        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro inesperado: {e}")


    def get_all_products(self):
        self.cursor.execute("SELECT id, nome, tipo, quantidade, preco, foto FROM produtos ORDER BY nome")
        return self.cursor.fetchall()


class LoginFrame(ctk.CTkFrame):
    # A classe LoginFrame permanece inalterada, pois já estava funcional.
    def __init__(self, master, login_callback):
        super().__init__(master)

        self.login_callback = login_callback
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure((0, 4), weight=1) 
        
        self.title_label = ctk.CTkLabel(self, text="🔑 Login do Armazém", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=1, column=0, pady=(20, 40))

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Usuário", width=200, height=40)
        self.username_entry.grid(row=2, column=0, pady=10)

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Senha", show="*", width=200, height=40)
        self.password_entry.grid(row=3, column=0, pady=10)

        self.login_button = ctk.CTkButton(self, text="Entrar", command=self.attempt_login, width=200, height=40)
        self.login_button.grid(row=5, column=0, pady=30)

    def attempt_login(self):
        user = self.username_entry.get()
        password = self.password_entry.get()
        
        # Credenciais fixas de exemplo
        if user == "admin" and password == "12345":
            self.login_callback() 
            self.username_entry.delete(0, 'end')
            self.password_entry.delete(0, 'end')
        else:
            messagebox.showerror("Erro de Login", "Usuário ou senha inválidos.")


class CadastroFrame(ctk.CTkFrame):
    # A classe CadastroFrame foi revisada para garantir a limpeza do estado
    def __init__(self, master, cadastro_callback):
        super().__init__(master)
        self.cadastro_callback = cadastro_callback
        self.selected_image_bytes = None # Armazena os bytes
        
        self.grid_columnconfigure((0, 1), weight=1) 
        
        self.title_label = ctk.CTkLabel(self, text="📦 Cadastro de Produtos (Bebidas)", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, columnspan=2, pady=(20, 30))

        # Entradas
        self.nome_label = ctk.CTkLabel(self, text="Nome da Bebida:")
        self.nome_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.nome_entry = ctk.CTkEntry(self, width=250)
        self.nome_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        self.tipo_label = ctk.CTkLabel(self, text="Tipo:")
        self.tipo_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.tipo_entry = ctk.CTkEntry(self, width=250)
        self.tipo_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        self.quantidade_label = ctk.CTkLabel(self, text="Quantidade (unidades):")
        self.quantidade_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.quantidade_entry = ctk.CTkEntry(self, width=250)
        self.quantidade_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        self.preco_label = ctk.CTkLabel(self, text="Preço (R$):")
        self.preco_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.preco_entry = ctk.CTkEntry(self, width=250)
        self.preco_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")

        # Foto
        self.foto_label = ctk.CTkLabel(self, text="Foto do Produto:")
        self.foto_label.grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.foto_button = ctk.CTkButton(self, text="Selecionar Foto", command=self.select_image)
        self.foto_button.grid(row=5, column=1, padx=10, pady=5, sticky="w")

        # Pré-visualização da Imagem
        self.image_display_label = ctk.CTkLabel(self, text="Nenhuma imagem selecionada", width=200, height=150,
                                               fg_color="gray70", text_color="gray30")
        self.image_display_label.grid(row=6, column=0, columnspan=2, pady=10)

        # Botão
        self.cadastrar_button = ctk.CTkButton(self, text="✅ Cadastrar Produto", command=self.submit_cadastro, height=40)
        self.cadastrar_button.grid(row=7, column=0, columnspan=2, pady=(40, 20), padx=20, sticky="ew")

    def select_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")])
        if file_path:
            try:
                img = Image.open(file_path)
                
                # CORREÇÃO: Usar o formato 'jpeg' ou 'png' ao salvar no buffer para garantir compatibilidade
                format_to_save = img.format if img.format in ['PNG', 'JPEG'] else 'PNG'
                
                img.thumbnail((200, 150)) 
                
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format=format_to_save) 
                self.selected_image_bytes = img_byte_arr.getvalue()

                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(200, 150))
                self.image_display_label.configure(image=ctk_img, text="")
                self.image_display_label.image = ctk_img 

            except Exception as e:
                messagebox.showerror("Erro de Imagem", f"Não foi possível carregar a imagem: {e}")
                self.selected_image_bytes = None
                self.image_display_label.configure(image=None, text="Nenhuma imagem selecionada", fg_color="gray70")


    def submit_cadastro(self):
        nome = self.nome_entry.get()
        tipo = self.tipo_entry.get()
        quantidade = self.quantidade_entry.get()
        preco = self.preco_entry.get()

        # Chama a função de cadastro (App.cadastrar_produto)
        self.cadastro_callback(nome, tipo, quantidade, preco, self.selected_image_bytes)
        
        # Limpa os campos após a TENTATIVA de cadastro (sucesso ou falha)
        self.nome_entry.delete(0, 'end')
        self.tipo_entry.delete(0, 'end')
        self.quantidade_entry.delete(0, 'end')
        self.preco_entry.delete(0, 'end')
        
        # ESSENCIAL: Limpa a imagem selecionada e o preview
        self.selected_image_bytes = None 
        self.image_display_label.configure(image=None, text="Nenhuma imagem selecionada", fg_color="gray70") 


class ViewProductsFrame(ctk.CTkFrame):
    # A classe ViewProductsFrame foi revisada para garantir melhor exibição de erros de imagem
    def __init__(self, master, get_products_callback):
        super().__init__(master)
        self.get_products_callback = get_products_callback

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) 

        self.title_label = ctk.CTkLabel(self, text="👀 Produtos Cadastrados", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, pady=(20, 10), sticky="w", padx=20)

        self.refresh_button = ctk.CTkButton(self, text="🔄 Atualizar Lista", command=self.load_products, width=150)
        self.refresh_button.grid(row=0, column=0, sticky="ne", padx=20, pady=20)

        self.scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Lista de Produtos:")
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        self.loaded_products = [] 

    def load_products(self):
        # Limpa e reseta
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.loaded_products = [] 

        products = self.get_products_callback()
        if not products:
            no_products_label = ctk.CTkLabel(self.scrollable_frame, text="Nenhum produto cadastrado ainda.")
            no_products_label.grid(row=0, column=0, pady=20)
            return

        for i, product in enumerate(products):
            product_id, nome, tipo, quantidade, preco, foto_bytes = product

            product_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
            product_frame.grid(row=i * 2, column=0, sticky="ew", pady=5, padx=5)
            product_frame.grid_columnconfigure(1, weight=1) 

            # --- Exibir Foto ---
            if foto_bytes:
                try:
                    img = Image.open(io.BytesIO(foto_bytes))
                    img.thumbnail((80, 80)) 
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(80, 80))
                    
                    self.loaded_products.append(ctk_img)

                    img_label = ctk.CTkLabel(product_frame, image=ctk_img, text="")
                    img_label.grid(row=0, column=0, rowspan=3, padx=10, pady=5, sticky="nw")
                    img_label.image = ctk_img 

                except Exception:
                    # Se houver erro ao ler o BLOB, usa um placeholder
                    placeholder_label = ctk.CTkLabel(product_frame, text="Erro Foto", width=80, height=80, 
                                                    fg_color="red", text_color="white", corner_radius=5)
                    placeholder_label.grid(row=0, column=0, rowspan=3, padx=10, pady=5, sticky="nw")
            else:
                # Placeholder para produtos sem foto
                placeholder_label = ctk.CTkLabel(product_frame, text="Sem Foto", width=80, height=80, 
                                                fg_color="gray50", text_color="white", corner_radius=5)
                placeholder_label.grid(row=0, column=0, rowspan=3, padx=10, pady=5, sticky="nw")

            # Detalhes do produto
            name_label = ctk.CTkLabel(product_frame, text=f"{nome}", font=ctk.CTkFont(size=16, weight="bold"))
            name_label.grid(row=0, column=1, padx=10, sticky="w")

            details_label = ctk.CTkLabel(product_frame, 
                                          text=f"Tipo: {tipo} | Qtd: {quantidade} | Preço: R${preco:.2f}")
            details_label.grid(row=1, column=1, padx=10, sticky="w")

            # Separador
            separator = ctk.CTkFrame(self.scrollable_frame, height=1, fg_color="gray60")
            separator.grid(row=i * 2 + 1, column=0, sticky="ew", pady=(5,0), padx=5)


if __name__ == "__main__":
    app = App()
    app.mainloop()
