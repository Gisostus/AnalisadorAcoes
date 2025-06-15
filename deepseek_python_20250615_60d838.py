import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser
import tempfile
import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
import ssl
import re

# Contornar problema de SSL
ssl._create_default_https_context = ssl._create_unverified_context

class AnalisadorAcoesReais:
    def __init__(self):
        self.janela = tk.Tk()
        self.janela.title("Analisador de Ações - Dados Reais")
        self.janela.geometry("500x450")
        self.janela.resizable(False, False)
        
        # Configurar interface
        self.configurar_interface()
        
        # Dados da ação atual
        self.dados_acao = None
        self.historico_precos = []
        self.dados_multiplos = []  # Para armazenar dados de múltiplas ações
        
    def configurar_interface(self):
        # Frame principal
        frame_principal = tk.Frame(self.janela, padx=20, pady=20)
        frame_principal.pack(fill='both', expand=True)
        
        # Título
        titulo = tk.Label(frame_principal, text="📈 Analisador de Ações", 
                         font=('Arial', 16, 'bold'))
        titulo.pack(pady=(0, 15))
        
        # Aviso da versão
        aviso = tk.Label(frame_principal, text="Conectando a fontes de dados reais", 
                        font=('Arial', 9), fg='green')
        aviso.pack(pady=(0, 15))
        
        # Frame para entrada de dados
        frame_entrada = tk.Frame(frame_principal)
        frame_entrada.pack(fill='x', pady=10)
        
        tk.Label(frame_entrada, text="Código da Ação:", 
                font=('Arial', 10, 'bold')).pack(anchor='w')
        
        # Frame para entrada e botão
        frame_input = tk.Frame(frame_entrada)
        frame_input.pack(fill='x', pady=(5, 0))

        self.entrada_acao = tk.Text(frame_input, font=('Arial', 10), width=20, height=3)
        self.entrada_acao.pack(side='left', fill='x', expand=True)
        self.entrada_acao.bind('<Control-Return>', lambda event: self.analisar_acao())
        
        # Botão de busca rápida
        self.botao_buscar = tk.Button(frame_input, text="🔍", 
                                     command=self.analisar_acao,
                                     font=('Arial', 10, 'bold'),
                                     width=3)
        self.botao_buscar.pack(side='right', padx=(5, 0))
        
        # Exemplo de códigos
        exemplo = tk.Label(frame_entrada,
                           text="Digite um código por linha:\nPETR4\nVALE3\nBBAS3",
                           font=('Arial', 8), fg='gray')
        exemplo.pack(anchor='w', pady=(5, 0))
        
        # Botões principais
        frame_botoes = tk.Frame(frame_principal)
        frame_botoes.pack(fill='x', pady=15)
        
        self.botao_analisar = tk.Button(frame_botoes, text="📊 Análise Detalhada", 
                                       command=self.analisar_acao,
                                       font=('Arial', 11, 'bold'),
                                       bg='#4CAF50', fg='white',
                                       height=2)
        self.botao_analisar.pack(side='left', fill='x', expand=True, padx=(0, 3))
        
        self.botao_grafico = tk.Button(frame_botoes, text="📈 Ver Gráfico", 
                                      command=self.mostrar_grafico,
                                      font=('Arial', 11, 'bold'),
                                      bg='#2196F3', fg='white',
                                      height=2)
        self.botao_grafico.pack(side='right', fill='x', expand=True, padx=(3, 0))
        
        # Área de resultados
        frame_resultado = tk.Frame(frame_principal)
        frame_resultado.pack(fill='both', expand=True, pady=10)
        
        tk.Label(frame_resultado, text="Resultados:", font=('Arial', 10, 'bold')).pack(anchor='w')
        
        # Frame para texto e scrollbar
        frame_texto = tk.Frame(frame_resultado)
        frame_texto.pack(fill='both', expand=True, pady=(5, 0))
        
        self.texto_resultado = tk.Text(frame_texto, height=10, width=50, 
                                      font=('Courier', 9), wrap=tk.WORD,
                                      bg='#f8f9fa', relief='solid', bd=1)
        self.texto_resultado.pack(side='left', fill='both', expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(frame_texto)
        scrollbar.pack(side='right', fill='y')
        self.texto_resultado.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.texto_resultado.yview)
        
        # Status
        self.status_label = tk.Label(frame_principal, text="Digite o código de uma ação para começar", 
                                   font=('Arial', 9), fg='gray')
        self.status_label.pack(pady=(10, 0))
        
    def formatar_codigo_acao(self, codigo):
        """Formatar código da ação para diferentes APIs"""
        codigo = codigo.strip().upper()
        # Remove .SA se presente
        if codigo.endswith('.SA'):
            codigo = codigo[:-3]
        return codigo
    
    def buscar_dados_yahoo_finance(self, simbolo):
        """Buscar dados do Yahoo Finance via web scraping"""
        try:
            # Tentar primeiro com yfinance se disponível
            try:
                import yfinance as yf
                ticker = yf.Ticker(f"{simbolo}.SA")
                info = ticker.info
                hist = ticker.history(period="5d")
                
                if hist.empty:
                    raise Exception("Sem dados históricos disponíveis")
                
                # Extrair dados
                preco_atual = float(hist['Close'].iloc[-1])
                preco_anterior = float(hist['Close'].iloc[-2]) if len(hist) > 1 else preco_atual
                volume = int(hist['Volume'].iloc[-1])
                alta = float(hist['High'].iloc[-1])
                baixa = float(hist['Low'].iloc[-1])
                
                # Criar histórico para gráfico
                historico = []
                for i, (data, row) in enumerate(hist.iterrows()):
                    historico.append({
                        'data': data.strftime('%d/%m'),
                        'preco': float(row['Close']),
                        'volume': int(row['Volume'])
                    })
                
                return {
                    'sucesso': True,
                    'fonte': 'Yahoo Finance (yfinance)',
                    'nome': info.get('longName', f"{simbolo} S.A."),
                    'simbolo': f"{simbolo}.SA",
                    'preco_atual': preco_atual,
                    'preco_anterior': preco_anterior,
                    'volume': volume,
                    'alta_dia': alta,
                    'baixa_dia': baixa,
                    'historico': historico,
                    'setor': info.get('sector', 'N/A'),
                    'mercado': info.get('market', 'B3')
                }
                
            except ImportError:
                # Se yfinance não está disponível, usar método alternativo
                return self.buscar_dados_alternativos(simbolo)
                
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e)
            }

    def buscar_dados_alternativos(self, simbolo):
        """Método alternativo usando APIs públicas"""
        try:
            # Tentar buscar da API do Yahoo Finance diretamente
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{simbolo}.SA"

            # Headers atualizados para simular um navegador moderno
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': f'https://finance.yahoo.com/quote/{simbolo}.SA',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site'
            }

            req = urllib.request.Request(url, headers=headers)

            # Aumentar timeout para 15 segundos
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status != 200:
                    error_msg = f"Erro HTTP {response.status}: {response.reason}"
                    return {'sucesso': False, 'erro': error_msg}

                data = json.loads(response.read().decode())

            # Verificar se a resposta contém dados válidos
            if 'chart' not in data or not data['chart']['result']:
                return {'sucesso': False, 'erro': "Resposta da API sem dados válidos"}

            result = data['chart']['result'][0]
            meta = result['meta']

            # Extrair preços com tratamento de dados ausentes
            timestamps = result.get('timestamp', [])
            quote = result['indicators']['quote'][0]
            precos = quote.get('close', [])
            volumes = quote.get('volume', [])
            altas = quote.get('high', [])
            baixas = quote.get('low', [])

            # Filtrar valores None e criar lista de dados válidos
            dados_validos = []
            for i in range(len(timestamps)):
                # Pular se preço ou volume forem nulos
                if precos[i] is None or volumes[i] is None:
                    continue

                dados_validos.append((
                    timestamps[i],
                    precos[i],
                    volumes[i],
                    altas[i] if i < len(altas) and altas[i] is not None else precos[i],
                    baixas[i] if i < len(baixas) and baixas[i] is not None else precos[i]
                ))

            if not dados_validos:
                return {'sucesso': False, 'erro': "Dados de preços não disponíveis"}

            # Pegar os dados mais recentes
            ultimo = dados_validos[-1]
            preco_atual = ultimo[1]
            volume_atual = ultimo[2]
            alta_atual = ultimo[3]
            baixa_atual = ultimo[4]

            # Obter preço anterior (se disponível)
            preco_anterior = dados_validos[-2][1] if len(dados_validos) > 1 else preco_atual

            # Criar histórico com os últimos 5 dias
            historico = []
            for dado in dados_validos[-5:]:
                timestamp, preco, volume, alta, baixa = dado
                data_obj = datetime.fromtimestamp(timestamp)
                historico.append({
                    'data': data_obj.strftime('%d/%m'),
                    'preco': round(preco, 2),
                    'volume': int(volume)
                })

            return {
                'sucesso': True,
                'fonte': 'Yahoo Finance API',
                'nome': meta.get('shortName', f"{simbolo} S.A."),
                'simbolo': f"{simbolo}.SA",
                'preco_atual': round(preco_atual, 2),
                'preco_anterior': round(preco_anterior, 2),
                'volume': int(volume_atual),
                'alta_dia': round(alta_atual, 2),
                'baixa_dia': round(baixa_atual, 2),
                'historico': historico,
                'setor': 'N/A',
                'mercado': 'B3'
            }

        except urllib.error.HTTPError as e:
            return {'sucesso': False, 'erro': f"Erro HTTP {e.code}: {e.reason}"}
        except urllib.error.URLError as e:
            return {'sucesso': False, 'erro': f"Erro de rede: {e.reason}"}
        except socket.timeout:
            return {'sucesso': False, 'erro': "Tempo limite de conexão excedido"}
        except json.JSONDecodeError:
            return {'sucesso': False, 'erro': "Resposta inválida da API"}
        except Exception as e:
            return {'sucesso': False, 'erro': f"Erro inesperado: {str(e)}"}
    
    def calcular_variacao(self, preco_atual, preco_anterior):
        """Calcular variação percentual"""
        if preco_anterior == 0:
            return 0
        return ((preco_atual - preco_anterior) / preco_anterior) * 100
    
    def calcular_rsi(self, precos, periodo=14):
        """Calcular RSI (Relative Strength Index)"""
        try:
            if len(precos) < periodo + 1:
                return None
            
            # Calcular mudanças de preço
            mudancas = []
            for i in range(1, len(precos)):
                mudancas.append(precos[i] - precos[i-1])
            
            # Separar ganhos e perdas
            ganhos = [max(0, mudanca) for mudanca in mudancas]
            perdas = [abs(min(0, mudanca)) for mudanca in mudancas]
            
            # Calcular médias móveis
            if len(ganhos) < periodo:
                return None
                
            media_ganhos = sum(ganhos[-periodo:]) / periodo
            media_perdas = sum(perdas[-periodo:]) / periodo
            
            # Evitar divisão por zero
            if media_perdas == 0:
                return 100
            
            # Calcular RS e RSI
            rs = media_ganhos / media_perdas
            rsi = 100 - (100 / (1 + rs))
            
            return round(rsi, 2)
            
        except Exception:
            return None
    
    def interpretar_rsi(self, rsi):
        """Interpretar valor do RSI"""
        if rsi is None:
            return "N/A", "gray"
        
        if rsi >= 70:
            return "SOBRECOMPRADO 🔴", "red"
        elif rsi <= 30:
            return "SOBREVENDIDO 🟢", "green"
        elif rsi >= 60:
            return "PRESSÃO DE VENDA 🟡", "orange"
        elif rsi <= 40:
            return "PRESSÃO DE COMPRA 🟡", "orange"
        else:
            return "NEUTRO ⚪", "gray"
    
    def calcular_medias_moveis(self, precos):
        """Calcular médias móveis simples"""
        try:
            if len(precos) < 20:
                return None, None
            
            # Média de 9 períodos (curto prazo)
            mm9 = sum(precos[-9:]) / 9 if len(precos) >= 9 else None
            
            # Média de 20 períodos (médio prazo)
            mm20 = sum(precos[-20:]) / 20 if len(precos) >= 20 else None
            
            return mm9, mm20
            
        except Exception:
            return None, None

    def buscar_dados_fundamentalistas(self, simbolo):
        """Buscar dados fundamentalistas da ação"""
        try:
            # Tentar buscar dados fundamentalistas do Yahoo Finance
            if hasattr(self, 'dados_acao') and self.dados_acao:
                # Tentar com yfinance se disponível
                try:
                    import yfinance as yf
                    ticker = yf.Ticker(f"{simbolo}.SA")
                    info = ticker.info

                    # Extrair dados fundamentalistas
                    dividends_per_share = info.get('dividendYield', 0)
                    earnings_per_share = info.get('trailingEps', 0)
                    payout_ratio = info.get('payoutRatio', 0)

                    return {
                        'dividendYield': dividends_per_share,
                        'trailingEps': earnings_per_share,
                        'payoutRatio': payout_ratio,
                        'bookValue': info.get('bookValue', 0),
                        'priceToBook': info.get('priceToBook', 0),
                        'returnOnEquity': info.get('returnOnEquity', 0)
                    }

                except ImportError:
                    # Método alternativo via API
                    url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{simbolo}.SA"
                    params = "?modules=defaultKeyStatistics,financialData,summaryDetail"

                    req = urllib.request.Request(url + params)
                    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

                    with urllib.request.urlopen(req, timeout=10) as response:
                        data = json.loads(response.read().decode())

                    result = data.get('quoteSummary', {}).get('result', [])
                    if result:
                        stats = result[0].get('defaultKeyStatistics', {})
                        financial = result[0].get('financialData', {})
                        summary = result[0].get('summaryDetail', {})

                        return {
                            'dividendYield': summary.get('dividendYield', {}).get('raw', 0),
                            'trailingEps': stats.get('trailingEps', {}).get('raw', 0),
                            'payoutRatio': stats.get('payoutRatio', {}).get('raw', 0),
                            'bookValue': stats.get('bookValue', {}).get('raw', 0),
                            'priceToBook': stats.get('priceToBook', {}).get('raw', 0),
                            'returnOnEquity': financial.get('returnOnEquity', {}).get('raw', 0)
                        }
                return None
                
        except Exception as e:
            print(f"Erro ao buscar dados fundamentalistas: {e}")
            return None

    def calcular_retention_ratio(self, dados_fundamentalistas):
        """Calcular Retention Ratio (Taxa de Retenção)"""
        try:
            if not dados_fundamentalistas:
                return None, "Dados insuficientes"

            payout_ratio = dados_fundamentalistas.get('payoutRatio', 0)

            # Se temos payout ratio, retention ratio = 1 - payout ratio
            if payout_ratio and payout_ratio > 0:
                retention_ratio = (1 - payout_ratio) * 100

                # Interpretação
                if retention_ratio >= 80:
                    interpretacao = "🚀 MUITO ALTA - Empresa reinveste fortemente"
                    cor = "green"
                elif retention_ratio >= 60:
                    interpretacao = "📈 ALTA - Foco em crescimento"
                    cor = "blue"
                elif retention_ratio >= 40:
                    interpretacao = "⚖️ MODERADA - Equilibrio crescimento/dividendos"
                    cor = "orange"
                elif retention_ratio >= 20:
                    interpretacao = "💰 BAIXA - Foco em dividendos"
                    cor = "purple"
                else:
                    interpretacao = "🔴 MUITO BAIXA - Distribui quase tudo"
                    cor = "red"

                return round(retention_ratio, 2), interpretacao

            # Método alternativo: usando dividend yield e ROE
            div_yield = dados_fundamentalistas.get('dividendYield', 0)
            roe = dados_fundamentalistas.get('returnOnEquity', 0)

            if div_yield and roe and roe > 0:
                # Estimativa baseada em dividend yield e ROE
                estimated_payout = (div_yield * 100) / (roe * 100)
                if 0 <= estimated_payout <= 1:
                    retention_ratio = (1 - estimated_payout) * 100
                    interpretacao = f"📊 ESTIMADO - Baseado em DY/ROE"
                    return round(retention_ratio, 2), interpretacao

            return None, "📊 Dados insuficientes para cálculo"

        except Exception as e:
            return None, f"❌ Erro no cálculo: {str(e)}"

    def processar_analise_individual(self, dados_acao, simbolo):
        """Processar análise individual de uma ação"""
        variacao = self.calcular_variacao(dados_acao['preco_atual'], dados_acao['preco_anterior'])

        precos_historicos = [item['preco'] for item in dados_acao.get('historico', [])]
        rsi = self.calcular_rsi(precos_historicos)
        rsi_interpretacao, rsi_cor = self.interpretar_rsi(rsi)
        mm9, mm20 = self.calcular_medias_moveis(precos_historicos)

        dados_fundamentalistas = self.buscar_dados_fundamentalistas(simbolo)
        retention_ratio, retention_interpretacao = self.calcular_retention_ratio(dados_fundamentalistas)

        return {
            'dados_acao': dados_acao,
            'variacao': variacao,
            'rsi': rsi,
            'rsi_interpretacao': rsi_interpretacao,
            'mm9': mm9,
            'mm20': mm20,
            'retention_ratio': retention_ratio,
            'retention_interpretacao': retention_interpretacao,
            'sucesso': True
        }

    def gerar_relatorio_multiplo(self, resultados):
        """Gerar relatório consolidado para múltiplas ações"""
        relatorio = f"""
    ╔══════════════════════════════════════════════╗
    ║            ANÁLISE DE MÚLTIPLAS AÇÕES        ║
    ╚══════════════════════════════════════════════╝

    📊 RESUMO: {len(resultados)} ações analisadas
    📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

    """

        # Separar sucessos e erros
        sucessos = [r for r in resultados if r.get('sucesso')]
        erros = [r for r in resultados if not r.get('sucesso')]

        if sucessos:
            relatorio += "┌─────────────── ANÁLISES REALIZADAS ──────────────┐\n"

            for resultado in sucessos:
                dados = resultado['dados_acao']
                variacao = resultado['variacao']
                rsi = resultado['rsi']

                tendencia_emoji = "🟢" if variacao > 0 else "🔴" if variacao < 0 else "🟡"

                relatorio += f"""
    📈 {dados['simbolo']}
       💰 R$ {dados['preco_atual']:.2f} ({variacao:+.2f}%) {tendencia_emoji}
       📊 RSI: {rsi if rsi else 'N/A'} | Vol: {dados['volume']:,}
       💎 Retention: {resultado['retention_ratio'] if resultado['retention_ratio'] else 'N/A'}%
       ──────────────────────────────
    """

            relatorio += "└──────────────────────────────────────────────────┘\n\n"

        if erros:
            relatorio += "┌─────────────── ERROS ENCONTRADOS ────────────────┐\n"
            for erro in erros:
                relatorio += f"❌ {erro['simbolo']}: {erro['erro']}\n"
            relatorio += "└──────────────────────────────────────────────────┘\n\n"

        # Ranking se houver múltiplos sucessos
        if len(sucessos) > 1:
            relatorio += self.gerar_ranking(sucessos)

        relatorio += """
    ⚠️  AVISO: Análise informativa, não constitui 
       recomendação de investimento.
    """

        self.texto_resultado.delete(1.0, tk.END)
        self.texto_resultado.insert(1.0, relatorio)

    def gerar_ranking(self, sucessos):
        """Gerar ranking das ações analisadas"""
        ranking = "\n┌─────────────── RANKING POR VARIAÇÃO ─────────────┐\n"

        # Ordenar por variação
        ordenados = sorted(sucessos, key=lambda x: x['variacao'], reverse=True)

        for i, resultado in enumerate(ordenados[:5]):  # Top 5
            dados = resultado['dados_acao']
            variacao = resultado['variacao']
            posicao = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i + 1}º"

            ranking += f"{posicao} {dados['simbolo']}: {variacao:+.2f}% (R$ {dados['preco_atual']:.2f})\n"

        ranking += "└──────────────────────────────────────────────────┘\n"
        return ranking

    def interpretar_retention_ratio(self, retention_ratio, setor="Geral"):
        """Interpretar Retention Ratio baseado no setor"""
        if retention_ratio is None:
            return "N/A"

        # Interpretações específicas por contexto
        interpretacoes = {
            "alta_tecnologia": {
                80: "Excelente para crescimento tecnológico",
                60: "Boa para inovação e expansão",
                40: "Moderada para tech estabelecida",
                20: "Baixa para setor tecnológico"
            },
            "utilities": {
                60: "Alta para setor de utilidades",
                40: "Típica para utilities maduras",
                20: "Esperada para utilities estáveis",
                0: "Muito baixa mas comum no setor"
            },
            "geral": {
                80: "Empresa em forte crescimento",
                60: "Foco em reinvestimento",
                40: "Equilibrio entre crescimento e dividendos",
                20: "Foco em distribuição de dividendos"
            }
        }

        categoria = interpretacoes.get(setor.lower(), interpretacoes["geral"])

        for limite, desc in sorted(categoria.items(), reverse=True):
            if retention_ratio >= limite:
                return desc

        return "Empresa distribui quase todos os lucros"

    def analisar_acao(self):
        """Analisar múltiplas ações"""
        codigos_texto = self.entrada_acao.get(1.0, tk.END).strip()

        if not codigos_texto:
            messagebox.showerror("Erro", "Por favor, digite pelo menos um código de ação.")
            return

        # Separar códigos por linha
        codigos = [codigo.strip().upper() for codigo in codigos_texto.split('\n') if codigo.strip()]

        if not codigos:
            messagebox.showerror("Erro", "Nenhum código válido encontrado.")
            return

        # Limitar a 10 ações para não sobrecarregar
        if len(codigos) > 10:
            messagebox.showwarning("Aviso", "Máximo de 10 ações por vez. Analisando as 10 primeiras.")
            codigos = codigos[:10]

        try:
            self.status_label.config(text=f"🔍 Analisando {len(codigos)} ações...", fg='blue')
            self.janela.update()

            resultados_completos = []

            for i, codigo_original in enumerate(codigos):
                self.status_label.config(text=f"🔍 Analisando {codigo_original} ({i + 1}/{len(codigos)})...",
                                         fg='blue')
                self.janela.update()

                simbolo = self.formatar_codigo_acao(codigo_original)
                resultado = self.buscar_dados_yahoo_finance(simbolo)

                if resultado['sucesso']:
                    # Processar cada ação individualmente
                    resultado_processado = self.processar_analise_individual(resultado, simbolo)
                    resultados_completos.append(resultado_processado)
                else:
                    resultados_completos.append({
                        'simbolo': simbolo,
                        'erro': resultado['erro'],
                        'sucesso': False
                    })

            # Gerar relatório consolidado
            self.gerar_relatorio_multiplo(resultados_completos)

            # Salvar para gráfico
            self.dados_multiplos = resultados_completos

            self.status_label.config(text=f"✅ {len(codigos)} ações analisadas", fg='green')

        except Exception as e:
            messagebox.showerror("Erro", f"Erro na análise: {str(e)}")
            self.status_label.config(text="❌ Erro na análise", fg='red')

    def mostrar_grafico(self):
        """Determinar qual tipo de gráfico mostrar"""
        if hasattr(self, 'dados_multiplos') and self.dados_multiplos:
            self.mostrar_grafico_multiplo()
        elif hasattr(self, 'dados_acao') and self.dados_acao:
            self.mostrar_grafico_individual()
        else:
            messagebox.showwarning("Aviso", "Analise uma ação primeiro.")

    def mostrar_grafico_individual(self):
        """Mostrar gráfico individual para uma ação"""
        if not hasattr(self, 'dados_acao') or not self.dados_acao:
            messagebox.showwarning("Aviso", "Analise uma ação primeiro.")
            return

        try:
            historico = self.dados_acao.get('historico', [])
            
            if not historico:
                messagebox.showwarning("Aviso", "Dados históricos não disponíveis para gráfico.")
                return
            
            # Calcular indicadores técnicos
            precos_historicos = [item['preco'] for item in historico]
            rsi_valores = []
            
            # Calcular RSI para cada ponto (se tiver dados suficientes)
            for i in range(len(precos_historicos)):
                if i >= 13:  # Precisa de pelo menos 14 pontos
                    rsi_ponto = self.calcular_rsi(precos_historicos[:i+1])
                    rsi_valores.append(rsi_ponto if rsi_ponto else 0)
                else:
                    rsi_valores.append(0)
            
            # Calcular médias móveis para cada ponto
            mm9_valores = []
            mm20_valores = []
            
            for i in range(len(precos_historicos)):
                if i >= 8:  # MM9
                    mm9_valores.append(sum(precos_historicos[max(0, i-8):i+1]) / min(9, i+1))
                else:
                    mm9_valores.append(None)
                    
                if i >= 19:  # MM20
                    mm20_valores.append(sum(precos_historicos[max(0, i-19):i+1]) / min(20, i+1))
                else:
                    mm20_valores.append(None)
            
            # Calcular variação atual
            variacao = self.calcular_variacao(
                self.dados_acao['preco_atual'], 
                self.dados_acao['preco_anterior']
            )

            # Calcular Retention Ratio para o gráfico
            dados_fundamentalistas = self.buscar_dados_fundamentalistas(
                self.formatar_codigo_acao(self.dados_acao['simbolo'].replace('.SA', '')))
            retention_ratio, retention_interpretacao = self.calcular_retention_ratio(dados_fundamentalistas)

            # Preparar dados para JavaScript
            labels = [item['data'] for item in historico]
            precos = [item['preco'] for item in historico]
            volumes = [item['volume'] for item in historico]
            
            # Determinar cor baseada na variação
            cor_linha = '#4CAF50' if variacao >= 0 else '#f44336'
            cor_fundo = 'rgba(76, 175, 80, 0.1)' if variacao >= 0 else 'rgba(244, 67, 54, 0.1)'

            # Criar HTML com gráfico interativo
            html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gráfico - {self.dados_acao['nome']}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{ 
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #2c3e50, #3498db);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .info-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            text-align: center;
        }}
        .info-card h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .info-card .value {{
            font-size: 1.8em;
            font-weight: bold;
            color: {cor_linha};
        }}
        .chart-container {{
            padding: 30px;
            background: white;
        }}
        .chart-wrapper {{
            position: relative;
            height: 400px;
            margin-bottom: 20px;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            background: #2c3e50;
            color: white;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 {self.dados_acao['nome']}</h1>
            <p>{self.dados_acao['simbolo']} • {self.dados_acao['mercado']}</p>
        </div>
        
        <div class="info-grid">
            <div class="info-card">
                <h3>Preço Atual</h3>
                <div class="value">R$ {self.dados_acao['preco_atual']:.2f}</div>
            </div>
            <div class="info-card">
                <h3>Variação</h3>
                <div class="value">{variacao:+.2f}%</div>
            </div>
            <div class="info-card">
                <h3>Retention Ratio</h3>
                <div class="value">{retention_ratio if retention_ratio else 'N/A'}{'%' if retention_ratio else ''}</div>
            </div>
            <div class="info-card">
                <h3>Volume</h3>
                <div class="value">{self.dados_acao['volume']:,}</div>
            </div>
            <div class="info-card">
                <h3>RSI (14)</h3>
                <div class="value">{self.calcular_rsi([item['preco'] for item in historico]) or 'N/A'}</div>
            </div>
            <div class="info-card">
                <h3>Tendência MM</h3>
                <div class="value" style="font-size: 1.2em;">{'📈' if mm9_valores[-1] and mm20_valores[-1] and mm9_valores[-1] > mm20_valores[-1] else '📉' if mm9_valores[-1] and mm20_valores[-1] and mm9_valores[-1] < mm20_valores[-1] else '➡️'}</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2 style="text-align: center; color: #2c3e50; margin-bottom: 30px;">
                📊 Evolução dos Preços + Médias Móveis
            </h2>
            <div class="chart-wrapper">
                <canvas id="graficoPrecos"></canvas>
            </div>
            
            <h2 style="text-align: center; color: #2c3e50; margin: 40px 0 30px 0;">
                🎯 RSI - Índice de Força Relativa
            </h2>
            <div class="chart-wrapper">
                <canvas id="graficoRSI"></canvas>
            </div>
            
            <h2 style="text-align: center; color: #2c3e50; margin: 40px 0 30px 0;">
                📊 Volume de Negociação
            </h2>
            <div class="chart-wrapper">
                <canvas id="graficoVolume"></canvas>
            </div>
        </div>
        
        <div class="footer">
            <p>⚠️ Dados obtidos de: {self.dados_acao['fonte']}</p>
            <p>📅 Atualizado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
            <p>💡 Este gráfico é apenas informativo e não constitui recomendação de investimento</p>
        </div>
    </div>
    
    <script>
        // Configuração comum dos gráficos
        Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        Chart.defaults.color = '#2c3e50';
        
        // Gráfico de Preços com Médias Móveis
        const ctxPrecos = document.getElementById('graficoPrecos').getContext('2d');
        const graficoPrecos = new Chart(ctxPrecos, {{
            type: 'line',
            data: {{
                labels: {json.dumps(labels)},
                datasets: [{{
                    label: 'Preço (R$)',
                    data: {json.dumps(precos)},
                    borderColor: '{cor_linha}',
                    backgroundColor: '{cor_fundo}',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '{cor_linha}',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 8
                }}, {{
                    label: 'MM9',
                    data: {json.dumps(mm9_valores)},
                    borderColor: '#ff6b6b',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4,
                    pointRadius: 2,
                    pointHoverRadius: 6
                }}, {{
                    label: 'MM20',
                    data: {json.dumps(mm20_valores)},
                    borderColor: '#4ecdc4',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4,
                    pointRadius: 2,
                    pointHoverRadius: 6
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                interaction: {{
                    intersect: false,
                    mode: 'index'
                }},
                plugins: {{
                    legend: {{
                        display: true,
                        position: 'top',
                        labels: {{
                            usePointStyle: true,
                            padding: 15
                        }}
                    }},
                    tooltip: {{
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '{cor_linha}',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: true,
                        callbacks: {{
                            label: function(context) {{
                                if (context.datasetIndex === 0) {{
                                    return 'Preço: R$ ' + context.parsed.y.toFixed(2);
                                }} else {{
                                    return context.dataset.label + ': R$ ' + (context.parsed.y ? context.parsed.y.toFixed(2) : 'N/A');
                                }}
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        grid: {{
                            display: true,
                            color: 'rgba(0,0,0,0.1)'
                        }},
                        title: {{
                            display: true,
                            text: 'Período'
                        }}
                    }},
                    y: {{
                        grid: {{
                            display: true,
                            color: 'rgba(0,0,0,0.1)'
                        }},
                        title: {{
                            display: true,
                            text: 'Preço (R$)'
                        }},
                        ticks: {{
                            callback: function(value) {{
                                return 'R$ ' + value.toFixed(2);
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // Gráfico do RSI
        const ctxRSI = document.getElementById('graficoRSI').getContext('2d');
        const graficoRSI = new Chart(ctxRSI, {{
            type: 'line',
            data: {{
                labels: {json.dumps(labels)},
                datasets: [{{
                    label: 'RSI',
                    data: {json.dumps(rsi_valores)},
                    borderColor: '#9b59b6',
                    backgroundColor: 'rgba(155, 89, 182, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#9b59b6',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 1,
                    pointRadius: 3,
                    pointHoverRadius: 6
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: true,
                        position: 'top'
                    }},
                    tooltip: {{
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#9b59b6',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {{
                            label: function(context) {{
                                return 'RSI: ' + context.parsed.y.toFixed(2);
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        grid: {{
                            display: true,
                            color: 'rgba(0,0,0,0.1)'
                        }},
                        title: {{
                            display: true,
                            text: 'Período'
                        }}
                    }},
                    y: {{
                        min: 0,
                        max: 100,
                        grid: {{
                            display: true,
                            color: 'rgba(0,0,0,0.1)'
                        }},
                        title: {{
                            display: true,
                            text: 'RSI (%)'
                        }},
                        ticks: {{
                            callback: function(value) {{
                                return value + '%';
                            }}
                        }}
                    }}
                }},
                elements: {{
                    line: {{
                        borderColor: function(context) {{
                            const value = context.parsed?.y;
                            if (value >= 70) return '#e74c3c';
                            if (value <= 30) return '#27ae60';
                            return '#9b59b6';
                        }}
                    }}
                }}
            }}
        }});
        
        // Gráfico de Volume
        const ctxVolume = document.getElementById('graficoVolume').getContext('2d');
        const graficoVolume = new Chart(ctxVolume, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(labels)},
                datasets: [{{
                    label: 'Volume',
                    data: {json.dumps(volumes)},
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: true,
                        position: 'top'
                    }},
                    tooltip: {{
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {{
                            label: function(context) {{
                                return 'Volume: ' + context.parsed.y.toLocaleString() + ' ações';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        grid: {{
                            display: false
                        }},
                        title: {{
                            display: true,
                            text: 'Período'
                        }}
                    }},
                    y: {{
                        grid: {{
                            display: true,
                            color: 'rgba(0,0,0,0.1)'
                        }},
                        title: {{
                            display: true,
                            text: 'Volume de Ações'
                        }},
                        ticks: {{
                            callback: function(value) {{
                                return value.toLocaleString();
                            }}
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
            
            # Salvar e abrir
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as f:
                f.write(html_content)
                caminho_html = f.name
            
            webbrowser.open('file://' + os.path.realpath(caminho_html))
            self.status_label.config(text="📈 Gráfico interativo aberto no navegador!", fg='green')
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar gráfico: {str(e)}")

    def mostrar_grafico_multiplo(self):
        """Mostrar gráfico comparativo para múltiplas ações"""
        try:
            # Filtrar apenas os sucessos
            sucessos = [r for r in self.dados_multiplos if r.get('sucesso')]

            if not sucessos:
                messagebox.showwarning("Aviso", "Nenhuma ação válida para gráfico.")
                return

            if len(sucessos) > 8:
                messagebox.showwarning("Aviso", "Limitando a 8 ações para melhor visualização.")
                sucessos = sucessos[:8]

            # Preparar dados
            acoes_dados = []
            cores = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336', '#00BCD4', '#795548', '#607D8B']

            for i, resultado in enumerate(sucessos):
                dados = resultado['dados_acao']
                variacao = resultado['variacao']

                acoes_dados.append({
                    'simbolo': dados['simbolo'],
                    'nome': dados['nome'][:30] + '...' if len(dados['nome']) > 30 else dados['nome'],
                    'preco_atual': dados['preco_atual'],
                    'variacao': variacao,
                    'volume': dados['volume'],
                    'historico': dados.get('historico', []),
                    'rsi': resultado.get('rsi'),
                    'retention_ratio': resultado.get('retention_ratio'),
                    'cor': cores[i % len(cores)]
                })

            # Criar HTML para gráfico múltiplo
            html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comparativo de Ações - {len(acoes_dados)} ações</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{ 
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #2c3e50, #3498db);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            padding: 20px;
            background: #f8f9fa;
        }}
        .stock-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            border-left: 4px solid var(--cor-acao);
        }}
        .stock-card h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
            font-size: 1.1em;
            font-weight: bold;
        }}
        .stock-price {{
            font-size: 1.5em;
            font-weight: bold;
            color: var(--cor-acao);
        }}
        .stock-variation {{
            font-size: 1.1em;
            margin-top: 5px;
        }}
        .chart-container {{
            padding: 30px;
            background: white;
        }}
        .chart-wrapper {{
            position: relative;
            height: 500px;
            margin-bottom: 30px;
        }}
        .chart-small {{
            height: 350px;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            background: #2c3e50;
            color: white;
            font-size: 0.9em;
        }}
        .positive {{ color: #4CAF50; }}
        .negative {{ color: #f44336; }}
        .neutral {{ color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Comparativo de Ações</h1>
            <p>{len(acoes_dados)} ações analisadas • Dados em tempo real</p>
        </div>

        <div class="summary-grid">"""

            # Adicionar cards das ações
            for acao in acoes_dados:
                variacao_class = 'positive' if acao['variacao'] > 0 else 'negative' if acao['variacao'] < 0 else 'neutral'
                html_content += f"""
            <div class="stock-card" style="--cor-acao: {acao['cor']}">
                <h3>{acao['simbolo']}</h3>
                <div class="stock-price">R$ {acao['preco_atual']:.2f}</div>
                <div class="stock-variation {variacao_class}">{acao['variacao']:+.2f}%</div>
                <small>Vol: {acao['volume']:,}</small>
            </div>"""

            html_content += f"""
        </div>

        <div class="chart-container">
            <h2 style="text-align: center; color: #2c3e50; margin-bottom: 30px;">
                📈 Comparativo de Preços Atuais
            </h2>
            <div class="chart-wrapper chart-small">
                <canvas id="graficoComparativo"></canvas>
            </div>

            <h2 style="text-align: center; color: #2c3e50; margin: 40px 0 30px 0;">
                📊 Variação Percentual do Dia
            </h2>
            <div class="chart-wrapper chart-small">
                <canvas id="graficoVariacao"></canvas>
            </div>

            <h2 style="text-align: center; color: #2c3e50; margin: 40px 0 30px 0;">
                🎯 Comparativo RSI
            </h2>
            <div class="chart-wrapper chart-small">
                <canvas id="graficoRSI"></canvas>
            </div>

            <h2 style="text-align: center; color: #2c3e50; margin: 40px 0 30px 0;">
                💎 Retention Ratio
            </h2>
            <div class="chart-wrapper chart-small">
                <canvas id="graficoRetention"></canvas>
            </div>

            <h2 style="text-align: center; color: #2c3e50; margin: 40px 0 30px 0;">
                📊 Volume de Negociação
            </h2>
            <div class="chart-wrapper chart-small">
                <canvas id="graficoVolume"></canvas>
            </div>
        </div>

        <div class="footer">
            <p>📅 Atualizado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
            <p>💡 Este comparativo é apenas informativo e não constitui recomendação de investimento</p>
        </div>
    </div>

    <script>
        Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        Chart.defaults.color = '#2c3e50';

        // Dados das ações
        const acoes = {json.dumps([{
            'simbolo': a['simbolo'],
            'preco': a['preco_atual'],
            'variacao': a['variacao'],
            'volume': a['volume'],
            'rsi': a['rsi'],
            'retention': a['retention_ratio'],
            'cor': a['cor']
        } for a in acoes_dados])};

        // Gráfico Comparativo de Preços
        const ctxComparativo = document.getElementById('graficoComparativo').getContext('2d');
        new Chart(ctxComparativo, {{
            type: 'bar',
            data: {{
                labels: acoes.map(a => a.simbolo),
                datasets: [{{
                    label: 'Preço Atual (R$)',
                    data: acoes.map(a => a.preco),
                    backgroundColor: acoes.map(a => a.cor + '80'),
                    borderColor: acoes.map(a => a.cor),
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return 'Preço: R$ ' + context.parsed.y.toFixed(2);
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: false,
                        title: {{
                            display: true,
                            text: 'Preço (R$)'
                        }},
                        ticks: {{
                            callback: function(value) {{
                                return 'R$ ' + value.toFixed(2);
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Gráfico de Variação
        const ctxVariacao = document.getElementById('graficoVariacao').getContext('2d');
        new Chart(ctxVariacao, {{
            type: 'bar',
            data: {{
                labels: acoes.map(a => a.simbolo),
                datasets: [{{
                    label: 'Variação (%)',
                    data: acoes.map(a => a.variacao),
                    backgroundColor: acoes.map(a => a.variacao >= 0 ? '#4CAF50' : '#f44336'),
                    borderColor: acoes.map(a => a.variacao >= 0 ? '#388E3C' : '#d32f2f'),
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return 'Variação: ' + context.parsed.y.toFixed(2) + '%';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        title: {{
                            display: true,
                            text: 'Variação (%)'
                        }},
                        ticks: {{
                            callback: function(value) {{
                                return value.toFixed(1) + '%';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Gráfico RSI
        const ctxRSI = document.getElementById('graficoRSI').getContext('2d');
        new Chart(ctxRSI, {{
            type: 'bar',
            data: {{
                labels: acoes.map(a => a.simbolo),
                datasets: [{{
                    label: 'RSI',
                    data: acoes.map(a => a.rsi || 0),
                    backgroundColor: acoes.map(a => {{
                        const rsi = a.rsi || 50;
                        if (rsi >= 70) return '#f44336';
                        if (rsi <= 30) return '#4CAF50';
                        return '#FF9800';
                    }}),
                    borderColor: acoes.map(a => a.cor),
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const rsi = context.parsed.y;
                                let status = 'Neutro';
                                if (rsi >= 70) status = 'Sobrecomprado';
                                else if (rsi <= 30) status = 'Sobrevendido';
                                return 'RSI: ' + rsi.toFixed(2) + ' (' + status + ')';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        min: 0,
                        max: 100,
                        title: {{
                            display: true,
                            text: 'RSI'
                        }},
                        ticks: {{
                            callback: function(value) {{
                                return value.toFixed(0);
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Gráfico Retention Ratio
        const ctxRetention = document.getElementById('graficoRetention').getContext('2d');
        new Chart(ctxRetention, {{
            type: 'bar',
            data: {{
                labels: acoes.map(a => a.simbolo),
                datasets: [{{
                    label: 'Retention Ratio (%)',
                    data: acoes.map(a => a.retention || 0),
                    backgroundColor: acoes.map(a => a.cor + '80'),
                    borderColor: acoes.map(a => a.cor),
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return 'Retention: ' + context.parsed.y.toFixed(2) + '%';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        min: 0,
                        max: 100,
                        title: {{
                            display: true,
                            text: 'Retention Ratio (%)'
                        }},
                        ticks: {{
                            callback: function(value) {{
                                return value.toFixed(0) + '%';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Gráfico Volume
        const ctxVolume = document.getElementById('graficoVolume').getContext('2d');
        new Chart(ctxVolume, {{
            type: 'bar',
            data: {{
                labels: acoes.map(a => a.simbolo),
                datasets: [{{
                    label: 'Volume',
                    data: acoes.map(a => a.volume),
                    backgroundColor: acoes.map(a => a.cor + '60'),
                    borderColor: acoes.map(a => a.cor),
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return 'Volume: ' + context.parsed.y.toLocaleString() + ' ações';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        title: {{
                            display: true,
                            text: 'Volume de Ações'
                        }},
                        ticks: {{
                            callback: function(value) {{
                                return value.toLocaleString();
                            }}
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

            # Salvar e abrir
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as f:
                f.write(html_content)
                caminho_html = f.name

            webbrowser.open('file://' + os.path.realpath(caminho_html))
            self.status_label.config(text="📊 Gráfico comparativo aberto no navegador!", fg='green')

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar gráfico múltiplo: {str(e)}")

    def executar(self):
        """Executar o aplicativo"""
        try:
            # Mensagem inicial
            self.texto_resultado.delete(1.0, tk.END)
            self.texto_resultado.insert(1.0, """
╔══════════════════════════════════════════════╗
║          BEM-VINDO AO ANALISADOR DE AÇÕES    ║
╚══════════════════════════════════════════════╝

🚀 RECURSOS DISPONÍVEIS:
   • Dados em tempo real da B3
   • Análise técnica básica
   • Gráficos interativos
   • Histórico de preços

📊 COMO USAR:
   1. Digite o código da ação (ex: PETR4)
   2. Clique em "Análise Detalhada"
   3. Veja o gráfico interativo

⚡ FONTES DE DADOS:
   • Yahoo Finance (principal)
   • APIs públicas de mercado
   • Dados atualizados em tempo real

💡 DICA: Experimente com:
   PETR4, VALE3, BBAS3, ITUB4, MGLU3, WEGE3

⚠️  IMPORTANTE:
   Este sistema é apenas informativo.
   Não constitui recomendação de investimento.

Digite uma ação acima para começar! 📈
""")
            
            self.janela.mainloop()
        except KeyboardInterrupt:
            self.janela.quit()


if __name__ == "__main__":
    print("🚀 Iniciando Analisador de Ações com Dados Reais...")
    print("📊 Conectando às fontes de dados de mercado...")
    
    # Verificar dependências opcionais
    try:
        import yfinance
        print("✅ yfinance disponível - Dados mais precisos")
    except ImportError:
        print("⚠️  yfinance não instalado - Usando método alternativo")
        print("💡 Para melhor precisão, instale: pip install yfinance")
    
    try:
        app = AnalisadorAcoesReais()
        app.executar()
    except Exception as e:
        print(f"❌ Erro ao iniciar aplicativo: {e}")
        input("Pressione Enter para sair...")