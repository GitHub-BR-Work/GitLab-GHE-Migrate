# Aqui está uma solução baseada em Python, assumindo que estamos referenciando apenas repositórios dentro da sua lista de projetos
# (não dentro de subgrupos, embora isso possa ser modificado para funcionar nesse caso).

# Essas etapas o guiarão através da parte difícil deste problema,
# fazendo com que os repositórios existam no GitHub (com o bônus adicional de copiar as descrições
# e combinar as configurações públicas/privadas).
# Para fazer isso, você terá que usar a API do GitHub ou criá-los manualmente.

# Pré-requisitos:

# configurar o Token da API do GitLab
# - https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#create-a-personal-access-token
# configurar o Token da API do GitHub
# - https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token

# Isso usará a solicitação GET de listagem de projetos do GitLab. Além disso, usará repetidamente
# a solicitação POST de criação de repositório do GitHub. Depois de executar isso (testado pessoalmente),
# você pode usar a lista de repositórios exibida no final e escrever um simples bash para iterar
# sobre eles clonando cada repositório, adicionando um git remote, e então fazendo push para o remote.
# Alternativamente, você poderia usar a opção --mirror acima. De qualquer forma, as opções são muitas neste ponto.

# Solicitação GET:
# - https://docs.gitlab.com/ee/api/projects.html#list-all-projects
# Solicitação POST:
# - https://docs.github.com/en/rest/repos/repos#create-a-repository-for-the-authenticated-user
# Adicionando Git Remote:
# - https://git-scm.com/docs/git-remote

# Nota: Este script não copiará quaisquer issues, PRs, ou outros metadados.
# Mas isso pode ser feito com a API do GitHub ou loop bash, se necessário.
# Você pode comentar "y=..." para ver o acesso aos repositórios do GitLab sem criar nada

# Código Python:

import shutil
import gitlab
from github import Github
import os
from git import Repo
import requests
import json
import subprocess

# Configurações do GitLab
gitlab_url = 'https://gitlab.com'  # URL do seu GitLab
gitlab_token = '$token-gitlab'  # Token de acesso para autenticação

# Configurações do GitHub
github_token = '$token-github'  # Token de acesso para autenticação no GitHub
github_organization = '$organization-github'  # Nome da organização no GitHub onde os repositórios serão criados

# ID do subgrupo que você deseja listar e exportar os repositórios
subgroup_id = $subgroup-gitlab  # Substitua pelo ID do seu subgrupo

# Nome de usuário para GitLab e GitHub
GITLAB_USERNAME = "<user>"
GITHUB_USERNAME = "<user>"

# Conectando ao GitLab
gl = gitlab.Gitlab(gitlab_url, private_token=gitlab_token)

# Obtendo o subgrupo específico
subgroup = gl.groups.get(subgroup_id)

# Conectando ao GitHub
gh = Github(github_token)

# Obtendo a organização do GitHub
org = gh.get_organization(github_organization)

# Listando e exportando os repositórios
print(f"Repositórios no subgrupo '{subgroup.full_name}':")
for project in subgroup.projects.list(all=True):
    print(project.name)
    # Definindo o caminho do diretório temporário
    repo_path = f"{project.name}_temp_clone"
    
    # Removendo o diretório temporário se ele já existir
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
    
    # Clonando o repositório do GitLab localmente
    Repo.clone_from(project.http_url_to_repo, repo_path)
    
    # Criando o repositório correspondente no GitHub como privado
    new_repo = org.create_repo(project.name, private=True)
    
    # Fazendo o push dos arquivos para o novo repositório no GitHub
    try:
        repo = Repo(repo_path)
        origin = repo.remote(name='origin')
        origin.set_url(new_repo.clone_url)
        origin.push()
    except Exception as e:
        print(f"Erro ao fazer push para {new_repo.name}: {e}")
    
    # Removendo o diretório temporário
    shutil.rmtree(repo_path)

print("Exportação concluída!")

# obtenha a lista de repositórios do gitlab
x = requests.get(
    url='https://gitlab.com/api/v4/users/{user}/projects'.format(user=GITLAB_USERNAME),
    headers={'PRIVATE-TOKEN': gitlab_token})
# imprima o código de resposta (200 é sucesso)
print(x)

repo_names = []
# itere os repositórios um a um
for repo in json.loads(x.content):
    # imprima os detalhes do repositório para ver o funcionamento
    print('Nome:', repo['name'])
    print('Descrição:', repo['description'])
    print('Visibilidade:', repo['visibility'])
    print('ssh_url_to_repo:', repo['ssh_url_to_repo'])

    repo_names.append(repo['name'])

    # crie o repositório no GitHub com o nome, descrição e configuração privada/pública
    y = requests.post(
        url='https://api.github.com/user/repos',
        headers={'Accept': 'application/vnd.github+json', 'Authorization': 'token {token}'.format(token=github_token)},
        json={'name': repo['name'], 'description': repo['description'], 'private': repo['visibility']=='private'})
    # imprima o código de resposta (201 é criado [sucesso])
    print(y)
    print('')

    # clone o repositório do GitLab
    subprocess.run(['git', 'clone', '--mirror', repo['ssh_url_to_repo']], check=True)

    # mude para o diretório recém-clonado
    os.chdir(repo['name'] + '.git')

    # faça push do espelho para o GitHub
    subprocess.run(['git', 'push', '--mirror', 'git@github.com:{user}/{repo}.git'.format(user=GITHUB_USERNAME, repo=repo['name'])], check=True)

    # volte para o diretório pai
    os.chdir('..')

    # remova o diretório clonado
    subprocess.run(['rmdir', '/S', '/Q', repo['name'] + '.git'], shell=True)

# imprima a lista de repositórios para referência
for name in repo_names:
    print(name)
