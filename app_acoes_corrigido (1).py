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
        
        self.entrada_acao = tk.Entry(frame_input, font=('Arial', 12), width=20)
        self.entrada_acao.pack(side='left', fill='x', expand=True)
        self.entrada_acao.bind('<Return>', lambda event: self.analisar_acao())
        
        # Botão de busca rápida
        self.botao_buscar = tk.Button(frame_input, text="🔍", 
                                     command=self.analisar_acao,
                                     font=('Arial', 10, 'bold'),
                                     width=3)
        self.botao_buscar.pack(side='right', padx=(5, 0))
        
        # Exemplo de códigos
        exemplo = tk.Label(frame_entrada, 
                          text="Exemplos: PETR4, VALE3, BBAS3, ITUB4, MGLU3 (sem .SA)", 
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
            
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            if 'chart' in data and data['chart']['result']:
                result = data['chart']['result'][0]
                meta = result['meta']
                
                # Extrair preços
                timestamps = result['timestamp']
                precos = result['indicators']['quote'][0]['close']
                volumes = result['indicators']['quote'][0]['volume']
                altas = result['indicators']['quote'][0]['high']
                baixas = result['indicators']['quote'][0]['low']
                
                # Filtrar valores None
                dados_validos = [(t, p, v, h, l) for t, p, v, h, l in 
                               zip(timestamps, precos, volumes, altas, baixas) 
                               if p is not None and v is not None]
                
                if not dados_validos:
                    raise Exception("Dados de preços não disponíveis")
                
                # Pegar os dados mais recentes
                ultimo_timestamp, preco_atual, volume_atual, alta_atual, baixa_atual = dados_validos[-1]
                preco_anterior = dados_validos[-2][1] if len(dados_validos) > 1 else preco_atual
                
                # Criar histórico
                historico = []
                for timestamp, preco, volume, alta, baixa in dados_validos[-7:]:  # Últimos 7 dias
                    data_obj = datetime.fromtimestamp(timestamp)
                    historico.append({
                        'data': data_obj.strftime('%d/%m'),
                        'preco': round(preco, 2),
                        'volume': volume or 0
                    })
                
                return {
                    'sucesso': True,
                    'fonte': 'Yahoo Finance API',
                    'nome': meta.get('shortName', f"{simbolo} S.A."),
                    'simbolo': f"{simbolo}.SA",
                    'preco_atual': round(preco_atual, 2),
                    'preco_anterior': round(preco_anterior, 2),
                    'volume': volume_atual or 0,
                    'alta_dia': round(alta_atual, 2) if alta_atual else preco_atual,
                    'baixa_dia': round(baixa_atual, 2) if baixa_atual else preco_atual,
                    'historico': historico,
                    'setor': 'N/A',
                    'mercado': 'B3'
                }
                
        except Exception as e:
            return {
                'sucesso': False,
                'erro': f"Erro ao buscar dados: {str(e)}"
            }
    
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
    
    def analisar_acao(self):
        """Analisar ação selecionada"""
        codigo_original = self.entrada_acao.get().strip()
        
        if not codigo_original:
            messagebox.showerror("Erro", "Por favor, digite o código da ação.")
            return
        
        try:
            # Atualizar status
            self.status_label.config(text="🔍 Buscando dados em tempo real...", fg='blue')
            self.janela.update()
            
            # Formatar código
            simbolo = self.formatar_codigo_acao(codigo_original)
            
            # Buscar dados
            resultado = self.buscar_dados_yahoo_finance(simbolo)
            
            if not resultado['sucesso']:
                raise Exception(resultado['erro'])
            
            self.dados_acao = resultado
            
            # Calcular variação
            variacao = self.calcular_variacao(
                self.dados_acao['preco_atual'], 
                self.dados_acao['preco_anterior']
            )
            
            # Calcular RSI e médias móveis
            precos_historicos = [item['preco'] for item in self.dados_acao.get('historico', [])]
            rsi = self.calcular_rsi(precos_historicos)
            rsi_interpretacao, rsi_cor = self.interpretar_rsi(rsi)
            mm9, mm20 = self.calcular_medias_moveis(precos_historicos)
            
            # Determinar tendência
            if variacao > 2:
                tendencia = "🟢 FORTE ALTA"
                cor_tendencia = "green"
            elif variacao > 0:
                tendencia = "🟢 ALTA"
                cor_tendencia = "green"
            elif variacao < -2:
                tendencia = "🔴 FORTE BAIXA"
                cor_tendencia = "red"
            elif variacao < 0:
                tendencia = "🔴 BAIXA"
                cor_tendencia = "red"
            else:
                tendencia = "🟡 ESTÁVEL"
                cor_tendencia = "orange"
            
            # Análise de volume
            volume_status = "Alto" if self.dados_acao['volume'] > 1000000 else "Baixo"
            volatilidade = "Alta" if abs(variacao) > 3 else "Baixa"
            
            # Análise de médias móveis
            if mm9 and mm20:
                if mm9 > mm20:
                    tendencia_mm = "🟢 TENDÊNCIA DE ALTA"
                elif mm9 < mm20:
                    tendencia_mm = "🔴 TENDÊNCIA DE BAIXA"
                else:
                    tendencia_mm = "🟡 TENDÊNCIA LATERAL"
                
                suporte_resistencia = f"MM9: R$ {mm9:.2f} | MM20: R$ {mm20:.2f}"
            else:
                tendencia_mm = "📊 DADOS INSUFICIENTES"
                suporte_resistencia = "N/A"
            
            # Formatar resultados
            resultado_texto = f"""
╔══════════════════════════════════════════════╗
║                 ANÁLISE DA AÇÃO              ║
╚══════════════════════════════════════════════╝

🏢 EMPRESA: {self.dados_acao['nome']}
📊 CÓDIGO: {self.dados_acao['simbolo']}
🏪 MERCADO: {self.dados_acao['mercado']}
📈 FONTE: {self.dados_acao['fonte']}

┌─────────────── COTAÇÃO ATUAL ───────────────┐
│ 💰 PREÇO: R$ {self.dados_acao['preco_atual']:.2f}                          │
│ 📊 VARIAÇÃO: {variacao:+.2f}%                       │
│ 🎯 TENDÊNCIA: {tendencia}                    │
└──────────────────────────────────────────────┘

┌─────────────── DADOS DO DIA ────────────────┐
│ 📈 MÁXIMA: R$ {self.dados_acao['alta_dia']:.2f}                         │
│ 📉 MÍNIMA: R$ {self.dados_acao['baixa_dia']:.2f}                         │
│ 📊 VOLUME: {self.dados_acao['volume']:,} ações          │
│ 🔊 LIQUIDEZ: {volume_status}                           │
└──────────────────────────────────────────────┘

┌──────────── ANÁLISE TÉCNICA ────────────────┐
│ 📊 VOLATILIDADE: {volatilidade}                        │
│ 💹 AMPLITUDE: R$ {(self.dados_acao['alta_dia'] - self.dados_acao['baixa_dia']):.2f}                         │
│ 📈 MOMENTUM: {'Positivo' if variacao > 0 else 'Negativo' if variacao < 0 else 'Neutro'}                          │
│ 🎯 RSI (14): {rsi if rsi else 'N/A'}                           │
│ 📊 STATUS RSI: {rsi_interpretacao}              │
│ 📈 MÉDIAS MÓVEIS: {tendencia_mm}           │
│ 🎯 SUPORTE/RESIST.: {suporte_resistencia}     │
└──────────────────────────────────────────────┘

⚠️  AVISO IMPORTANTE:
   Esta análise é baseada em dados de mercado em
   tempo real, mas não constitui recomendação de
   investimento. Consulte sempre um especialista.

📅 Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
"""
            
            # Mostrar resultados
            self.texto_resultado.delete(1.0, tk.END)
            self.texto_resultado.insert(1.0, resultado_texto)
            
            # Atualizar status
            self.status_label.config(text=f"✅ Dados atualizados para {simbolo}.SA", fg='green')
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao analisar ação:\n{str(e)}\n\nVerifique:\n• Código da ação está correto\n• Conexão com internet\n• Ação existe na B3")
            self.status_label.config(text="❌ Erro na análise", fg='red')
    
    def mostrar_grafico(self):
        """Mostrar gráfico interativo com dados reais"""
        if not self.dados_acao:
            messagebox.showwarning("Aviso", "Primeiro analise uma ação para ver o gráfico!")
            return
        
        try:
            # Preparar dados para o gráfico
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
                }},
                // Adicionar linhas de referência para RSI
                annotation: {{
                    annotations: {{
                        sobrecomprado: {{
                            type: 'line',
                            yMin: 70,
                            yMax: 70,
                            borderColor: '#e74c3c',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            label: {{
                                content: 'Sobrecomprado (70)',
                                enabled: true,
                                position: 'end'
                            }}
                        }},
                        sobrevendido: {{
                            type: 'line',
                            yMin: 30,
                            yMax: 30,
                            borderColor: '#27ae60',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            label: {{
                                content: 'Sobrevendido (30)',
                                enabled: true,
                                position: 'end'
                            }}
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
            