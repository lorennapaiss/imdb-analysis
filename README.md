
# 🎬 IMDb Top 1000 — Análise Exploratória de Dados

## 📌 Visão Geral

Este projeto realiza uma **Análise Exploratória de Dados (EDA)** sobre o dataset dos **1000 filmes mais bem avaliados do IMDb**, com foco em compreender **quais fatores estão associados à qualidade percebida**, popularidade e desempenho geral dos títulos.

O objetivo vai além de explorar dados: busca **transformar dados reais em insights claros e defensáveis**, utilizando boas práticas de análise, limpeza e comunicação analítica.

---

## 🎯 Objetivos

* Analisar padrões de **avaliação (IMDb Rating)**, **popularidade (número de votos)** e **crítica especializada (Metascore)**
* Investigar relações entre **duração**, **gênero**, **década de lançamento** e **avaliação**
* Avaliar se **sucesso financeiro** está associado à qualidade percebida
* Produzir um notebook **reproduzível, bem documentado e pronto para portfólio**

---

## 🗂️ Dataset

* **Fonte:** Kaggle — *IMDb Dataset of Top 1000 Movies and TV Shows*
* **Acesso:** via `kagglehub`
* **Registros:** 1000 títulos

**Principais colunas**

* `series_title`, `released_year`, `genre`
* `imdb_rating`, `meta_score`, `no_of_votes`
* `runtime_min`, `gross`
* `director`, `star1`, `star2`, `star3`, `star4`

⚠️ Trata-se de um dataset **altamente selecionado**, comparando títulos bons vs excelentes.

---

## 🛠️ Tecnologias Utilizadas

* Python
* Pandas
* Matplotlib
* Jupyter Notebook
* kagglehub
* Ambiente virtual (`venv`)

---

## 🧠 Metodologia

1. **Auditoria de dados**

   * Tipos, valores ausentes e duplicatas
2. **Limpeza e padronização**

   * Conversões seguras de tipos
   * Tratamento explícito de nulos
3. **Feature engineering**

   * Décadas de lançamento
   * Receita em milhões
   * Explode de gêneros
4. **Análise exploratória**

   * Distribuições
   * Rankings
   * Correlações
   * Análises por grupo (gênero, década, diretores e atores)
5. **Síntese de insights**

   * Conclusões claras e defensáveis

---

## 📊 Principais Insights

* A **nota média do dataset é 7,95**, com valores entre **7,6 e 9,3**
* A relação entre **duração e avaliação** é **fraca**
* Existe **correlação moderada** entre **popularidade (votos)** e **avaliação**
* **Crítica e público** apresentam **alinhamento parcial**
* **Sucesso financeiro não garante alta avaliação**
* Gêneros como **Drama, War, Sci-Fi e Mystery** apresentam maiores médias de nota
* Filmes recentes entram mais rapidamente no Top 1000, sem evidência de superioridade histórica

**Conclusão central:**
A qualidade percebida no IMDb é resultado de **múltiplos fatores combinados**, e não de um único elemento isolado.

---

## 📁 Estrutura do Projeto

```
imdb-analysis/
│
├── data/
│   └── imdb_top_1000.csv
│
├── notebooks/
│   └── analise_imdb.ipynb
│
├── images/
│   └── graficos.png
│
├── README.md
└── requirements.txt
```

---

## ▶️ Como Executar Localmente

### Criar e ativar o ambiente virtual

Linux / macOS:

```
python -m venv venv
source venv/bin/activate
```

Windows (PowerShell):

```
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Instalar dependências

```
pip install --upgrade pip
pip install -r requirements.txt
```

### Executar o notebook

```
jupyter notebook
```

Selecione o kernel do ambiente virtual antes de rodar as células.

---

## ⚠️ Limitações

* Dataset restrito aos **Top 1000 títulos**
* Dados de receita incompletos
* Ausência de ajuste por inflação ou contexto histórico

---

## 🔜 Próximos Passos

* Criar dashboard interativo
* Explorar modelos preditivos simples
* Integrar dados externos (APIs)

---

## 👤 Autora

**Lorenna Pais**
Analista de Dados



