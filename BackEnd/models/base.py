#criando a classe base abstrata do projeto
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from enum import Enum #utilizado para definir conjunto finito de valores

#criando o tipo do usuario(enum) e garantindo que nao terá strings avulsas, sem um valor conhecido
class TipoUsuario(Enum):
    DOADOR = "DOADOR"
    BENEFICIARIO = "BENEFICIARIO"
    ADMINISTRADOR = "ADMINISTRADOR"

#criando e garantindo que o StatusUsuario seja apenas ativo, inativo, pendente ou bloqueado
class StatusUsuario(Enum):
    ATIVO = "ATIVO"
    INATIVO = "INATIVO"
    PENDENTE = "PENDENTE"
    BLOQUEADO = "BLOQUEADO"

#criando a base Perfil e declarando como abstrata, pois quando aplicar em Doador, Beneficiario e Admistrador deverá herdar métodos específicos
class PerfilUsuario(ABC): 
    #criando os atributos da classe e definindo como _... para que nao seja permitido alterar o valor de forma externa
    def __init__(self, id_usuario: int, nome: str, email: str, telefone: str, cep: str, tipo_usuario: TipoUsuario):
        self._id_usuario = id_usuario
        self._nome = nome
        self._email = email
        self._telefone = telefone
        self._cep = cep
        self._tipo_usuario = tipo_usuario
        self._status = StatusUsuario.ATIVO
    
    #criando os getters e setters de cada atributo
    @property
    def id_usuario(self) -> int:
        return self._id_usuario

    @property
    def nome(self) -> str:
        return self._nome

    @nome.setter
    def nome(self, valor: str) -> None:
        if not valor or len(valor.strip()) < 3:
            #garantindo que seja um nome Valido
            raise ValueError("Nome deve ter pelo menos 3 caracteres")
        self._nome = valor.strip()

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, valor: str) -> None:
        if "@" not in valor:
            #garantindo que seja um email valido
            raise ValueError("Email inválido")
        self._email = valor.strip().lower()

    @property
    def telefone(self) -> str:
        return self._telefone

    @telefone.setter
    def telefone(self, valor: str) -> None:
        self._telefone = valor

    @property
    def cep(self) -> str:
        return self._cep

    @property
    def tipo_usuario(self) -> TipoUsuario:
        return self._tipo_usuario

    @property
    def status(self) -> StatusUsuario:
        return self._status

    @status.setter
    def status(self, valor: StatusUsuario) -> None:
        self._status = valor

    #criando o metodo para que todo Usuario consiga gerar um resumo completo do seu perfil
    @abstractmethod
    def obter_resumo(self) -> Dict[str, Any]:
        raise NotImplementedError

    #criando o metodo para que todo Usuario consiga validar se o seu perfil esta tudo completo
    @abstractmethod
    def validar_perfil(self) -> bool:
        raise NotImplementedError

    #ativando o perfil do usuario
    def ativar(self) -> None:
        self._status = StatusUsuario.ATIVO

    #desativando o perfil do usuario
    def desativar(self) -> None:
        self._status = StatusUsuario.INATIVO

    #bloquando o perfil do usuario
    def bloquear(self) -> None:
        self._status = StatusUsuario.BLOQUEADO

    #Print de como sera mostrado as informações necessarias do usuario
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self._id_usuario} nome='{self._nome}' status={self._status.value}>"