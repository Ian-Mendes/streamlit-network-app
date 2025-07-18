import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt
import kagglehub

from kagglehub import KaggleDatasetAdapter

def st_pyvis(graph):
    net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white")
    net.from_nx(graph)
    net.save_graph("pyvis_graph.html")
    with open("pyvis_graph.html", "r", encoding="utf-8") as f:
        html = f.read()
    st.components.v1.html(html, height=600, scrolling=True)

def main():
    st.title("Análise Interativa de Redes com Pyvis e Streamlit")

    # ===============================
    # Carregamento dos dados
    # ===============================
    st.subheader("📦 Carregando dados do Kaggle")
    file_path = "affiliation.csv"
    affiliation = kagglehub.load_dataset(
        KaggleDatasetAdapter.PANDAS,
        "marthadimgba/spy-agency-dataset-2024",
        file_path,
    )

    file_path = "affiliationrel.csv"
    affiliationrel = kagglehub.load_dataset(
        KaggleDatasetAdapter.PANDAS,
        "marthadimgba/spy-agency-dataset-2024",
        file_path,
    )

    file_path = "agent.csv"
    agent = kagglehub.load_dataset(
        KaggleDatasetAdapter.PANDAS,
        "marthadimgba/spy-agency-dataset-2024",
        file_path,
    )

    # ===============================
    # Construção do grafo
    # ===============================
    Grafo = nx.Graph()
    for _, row in agent.iterrows():
        node_id = f"agent_{row['agent_id']}"
        Grafo.add_node(
            node_id,
            label=f"{row['first_name']} {row['last_name']}",
            type='agent',
            address=row['address'],
            city=row['city'],
            country=row['country'],
            salary=row['salary']
        )

    for _, row in affiliation.iterrows():
        node_id = f"aff_{row['affiliation_id']}"
        Grafo.add_node(
            node_id,
            label=row['affiliation_name'],
            type='affiliation',
            description=row['description']
        )

    for _, row in affiliationrel.iterrows():
        agent_node = f"agent_{row['agent_id']}"
        aff_node = f"aff_{row['affiliation_id']}"
        if agent_node in Grafo.nodes and aff_node in Grafo.nodes:
            Grafo.add_edge(
                agent_node,
                aff_node,
                affiliation_strength=row['affiliation_strength']
            )

    # ===============================
    # Métricas Estruturais
    # ===============================
    st.subheader("📊 Métricas Estruturais")
    st.write(f"Densidade: {nx.density(Grafo):.4f}")
    st.write(f"Coeficiente de clustering global: {nx.transitivity(Grafo):.4f}")

    try:
        assort = nx.degree_pearson_correlation_coefficient(Grafo)
        st.write(f"Assortatividade: {assort:.4f}")
    except Exception as e:
        st.warning("Não foi possível calcular a assortatividade.")
        st.info(f"Possíveis motivos: grafo bipartido, pouca variação de grau ou estrutura muito regular. Erro: {e}")

    if Grafo.is_directed():
        scc = nx.number_strongly_connected_components(Grafo)
        wcc = nx.number_weakly_connected_components(Grafo)
        st.write(f"Componentes fortemente conectados: {scc}")
        st.write(f"Componentes fracamente conectados: {wcc}")
    else:
        cc = nx.number_connected_components(Grafo)
        st.write(f"Componentes conectados: {cc}")

    # ===============================
    # Distribuição de Grau
    # ===============================
    st.subheader("📈 Distribuição de Grau dos Nós")
    graus = [deg for node, deg in Grafo.degree()]
    plt.figure(figsize=(8,6))
    plt.hist(graus, bins=range(1, max(graus)+2), edgecolor='black')
    plt.title('Distribuição de Grau dos Nós')
    plt.xlabel('Grau')
    plt.ylabel('Frequência')
    st.pyplot(plt.gcf())

    # ===============================
    # Centralidade dos Nós
    # ===============================
    st.subheader("🔝 Centralidade dos Nós")

    degree_centrality = nx.degree_centrality(Grafo)
    eigenvector_centrality = nx.eigenvector_centrality(Grafo, max_iter=1000)
    closeness_centrality = nx.closeness_centrality(Grafo)
    betweenness_centrality = nx.betweenness_centrality(Grafo)

    centrality_options = {
        "Degree": degree_centrality,
        "Eigenvector": eigenvector_centrality,
        "Closeness": closeness_centrality,
        "Betweenness": betweenness_centrality
    }

    selected_centrality = st.selectbox("Escolha a métrica:", list(centrality_options.keys()))
    top_k = st.slider("Top-k nós mais centrais:", min_value=3, max_value=20, value=5)

    centrality_dict = centrality_options[selected_centrality]
    sorted_nodes = sorted(centrality_dict.items(), key=lambda x: x[1], reverse=True)[:top_k]
    for node, val in sorted_nodes:
        st.write(f"{node}: {val:.4f}")

    # ===============================
    # Subgrafo principal
    # ===============================
    st.subheader("🌐 Visualização Interativa da Rede")
    option = st.selectbox("Escolha o subgrafo a visualizar:", ["Grafo completo", "Maior componente conectada"])
    if option == "Maior componente conectada":
        largest_cc = max(nx.connected_components(Grafo), key=len)
        subgraph = Grafo.subgraph(largest_cc)
        st.write(f"Maior componente: {subgraph.number_of_nodes()} nós, {subgraph.number_of_edges()} arestas")
        st_pyvis(subgraph)
    else:
        st_pyvis(Grafo)

if __name__ == "__main__":
    main()