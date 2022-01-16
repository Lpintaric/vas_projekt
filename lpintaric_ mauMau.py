#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from time import sleep
from spade.agent import Agent
import random
from spade.behaviour import FSMBehaviour, State
from spade.message import Message
import spade
import asyncio
import ast

spilKarata = [
    "Z_7", "Z_8", "Z_9", "Z_X", "Z_J", "Z_Q", "Z_K", "Z_A",
    "P_7", "P_8", "P_9", "P_X", "P_J", "P_Q", "P_K", "P_A",
    "K_7", "K_8", "K_9", "K_X", "K_J", "K_Q", "K_K", "K_A",
    "S_7", "S_8", "S_9", "S_X", "S_J", "S_Q", "S_K", "S_A",
    ]
stol = []

class Igrac(Agent):
    def postaviParametre(self, igrac, primatelj, pocetak):
        self.igrac = igrac
        self.primatelj = primatelj
        self.pocetak = pocetak
        self.uzmi = 0

    class KonacniAutomat(FSMBehaviour):
        async def on_start(self):
            print(f"{self.agent.igrac} : spreman sam za igru")
            print("--------------------------------------------------------------------------")
    class CekajKarte(State):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                self.agent.ruka = ast.literal_eval(msg.body)
                print(f"{self.agent.igrac} : dobivene karte : {self.agent.ruka}")
            else:
                print(f"{self.agent.igrac} : nisam dobio karte")
            print("--------------------------------------------------------------------------")
            if(self.agent.pocetak):
                self.set_next_state("OdigrajKartu")
            else:
                self.set_next_state("CekajPotez")
    
    class CekajPotez(State):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                if(msg.body == "NEMAM_KARTE"):
                    await self.agent.stop()
                elif(msg.body == "TVOJ_POTEZ"):
                    self.set_next_state("OdigrajKartu")
                elif(msg.body.find("UZMI") >= 0):
                    self.agent.uzmi = int(msg.body[-1])
                    self.set_next_state("OdigrajKartuSedmica")
                elif(msg.body == "PRESKACEM_TE"):
                    self.set_next_state("PropustiPotez")
            else:
                print(f"{self.agent.igrac} : predugo sam cekao")

    class OdigrajKartu(State):
        async def run(self):
            await asyncio.sleep(1)
            
            if(len(self.agent.ruka) <= 0):
                await self.potvrdiPobjedu()
                await self.agent.stop()
            else:
                await self.odigrajKartu()

            print(f"{self.agent.igrac} : preostale karte {self.agent.ruka}")
            print("--------------------------------------------------------------------------")
        
        async def potvrdiPobjedu(self):
            await self.kontaktiraj(self.agent.primatelj, "NEMAM_KARTE")
            print(f"{self.agent.igrac} : nemam više karte, pobjedio sam!")
        
        async def odigrajKartu(self):
            global stol
            posljednjaKarta = stol[-1]
            boja = posljednjaKarta[0]
            tip = posljednjaKarta[2]

            karta = await self.odigrajOsmicu(boja, tip)
            if(karta != ""):
                await self.odigrajPotez(karta, "PRESKACEM_TE")
                print(f"{self.agent.igrac} : odigrao sam kartu " + karta + ", preskačem te")
                return
            
            karta = await self.odigrajSedmicu(boja, tip)
            if(karta != ""):
                await self.odigrajPotez(karta, "UZMI_2")
                print(f"{self.agent.igrac} : odigrao sam kartu " + karta + ", uzmi 2")
                return

            karta = await self.odigrajObicnu(boja, tip)
            if(karta != ""):
                await self.odigrajPotez(karta, "TVOJ_POTEZ")
                print(f"{self.agent.igrac} : odigrao sam kartu " + karta)
                return
            
            if(karta == ""):
                await self.uzmiKarte(1)
                await self.kontaktiraj(self.agent.primatelj, "TVOJ_POTEZ")
                self.set_next_state("CekajPotez")
                return

        async def odigrajOsmicu(self, boja, tip):
            for k in self.agent.ruka:
                b = k[0]
                t = k[2]
                if(t == "8"):
                    if(b == boja or t == tip):
                        return k
            return ""             
        
        async def odigrajSedmicu(self, boja, tip):
            karta = ""
            for k in self.agent.ruka:
                b = k[0]
                t = k[2]
                if(t == "7"):
                    if(b == boja or t == tip):
                        karta = k
                        return karta
            return karta
            

        async def odigrajObicnu(self, boja, tip):
            karta = ""
            for k in self.agent.ruka:
                b = k[0]
                t = k[2]
                if(b == boja or t == tip):
                    karta = k
                    return karta
            return karta
        
        async def odigrajPotez(self, karta, poruka):
            stol.append(karta)
            self.agent.ruka.remove(karta)
            await self.kontaktiraj(self.agent.primatelj, poruka)
            self.set_next_state("CekajPotez")

        async def uzmiKarte(self, broj):
            global spilKarata
            if(len(spilKarata) < broj):
                print(f"{self.agent.igrac} : saljem poruku nadzorniku")
                print("--------------------------------------------------------------------------")
                await self.kontaktiraj("agent@rec.foi.hr", "MIJESAJ")
                msg = await self.receive(timeout=100)
                if msg:
                    if(msg.body == "NASTAVI"):
                        print(f"{self.agent.igrac} : nastavljam")
            
            for i in range(0, broj):
                karta = spilKarata[-1]
                self.agent.ruka.append(karta)
                spilKarata.pop()
            print(f"{self.agent.igrac} : uzimam karte")

        async def kontaktiraj(self, primatelj, info):
            msg = Message(
                to=primatelj,
                body=f"{info}"
                )
            await self.send(msg)

    class OdigrajKartuSedmica(State):
        async def run(self):
            await asyncio.sleep(1)

            global stol
            posljednjaKarta = stol[-1]
            boja = posljednjaKarta[0]
            tip = posljednjaKarta[2]

            uzmi = self.agent.uzmi
            
            if(uzmi == 8):
                await self.uzmiKarte(8)
            else:
                karta = await self.odigrajSedmicu(boja, tip)
                if(karta != ""):
                    await self.odigrajPotez(karta, "UZMI_" + str(uzmi + 2))
                else:
                    await self.uzmiKarte(uzmi)

            print(f"{self.agent.igrac} : preostale karte {self.agent.ruka}")
            print("--------------------------------------------------------------------------")
            self.set_next_state("CekajPotez")
            self.agent.uzmi = 0
        
        async def odigrajSedmicu(self, boja, tip):
            karta = ""
            for k in self.agent.ruka:
                b = k[0]
                t = k[2]
                if(t == "7"):
                    if(b == boja or t == tip):
                        karta = k
                        return karta
            return karta
        
        async def odigrajPotez(self, karta, poruka):
            stol.append(karta)
            self.agent.ruka.remove(karta)
            await self.kontaktiraj(self.agent.primatelj, poruka)
            print(f"{self.agent.igrac} : odigrao sam kartu " + karta + ", uzmi " + str(self.agent.uzmi + 2))

        async def uzmiKarte(self, broj):
            global spilKarata
            if(len(spilKarata) < broj):
                print(f"{self.agent.igrac} : molim promiješati karte !")
                print("--------------------------------------------------------------------------")
                await self.kontaktiraj("agent@rec.foi.hr", "MIJESAJ")
                msg = await self.receive(timeout=100)
                if msg:
                    if(msg.body == "NASTAVI"):
                        print(f"{self.agent.igrac} : Nastavljam")
            
            for i in range(0, broj):
                karta = spilKarata[-1]
                self.agent.ruka.append(karta)
                spilKarata.pop()
            print(f"{self.agent.igrac} : uzimam karte")
            await self.kontaktiraj(self.agent.primatelj, "TVOJ_POTEZ")


        async def kontaktiraj(self, primatelj, info):
            msg = Message(
                to=primatelj,
                body=f"{info}"
                )
            await self.send(msg)

        
    
    class PropustiPotez(State):
        async def run(self):
            await asyncio.sleep(1)
            await self.kontaktiraj(self.agent.primatelj, "TVOJ_POTEZ")
            self.set_next_state("CekajPotez")
            print(f"{self.agent.igrac} : propustio sam potez")
            print(f"{self.agent.igrac} : preostale karte {self.agent.ruka}")
            print("--------------------------------------------------------------------------")

        async def kontaktiraj(self, primatelj, info):
            msg = Message(
                to=primatelj,
                body=f"{info}"
                )
            await self.send(msg)


    async def setup(self):
        fsm = self.KonacniAutomat()
        fsm.add_state(name="CekajKarte", state=self.CekajKarte(), initial=True)
        fsm.add_state(name="OdigrajKartu", state=self.OdigrajKartu())
        fsm.add_state(name="CekajPotez", state=self.CekajPotez())
        fsm.add_state(name="OdigrajKartuSedmica", state=self.OdigrajKartuSedmica())
        fsm.add_state(name="PropustiPotez", state=self.PropustiPotez())
        fsm.add_transition(source="CekajKarte", dest="OdigrajKartu") 
        fsm.add_transition(source="CekajKarte", dest="CekajPotez")
        fsm.add_transition(source="OdigrajKartu", dest="CekajPotez")
        fsm.add_transition(source="CekajPotez", dest="OdigrajKartu")
        fsm.add_transition(source="CekajPotez", dest="OdigrajKartuSedmica")
        fsm.add_transition(source="OdigrajKartuSedmica", dest="CekajPotez")
        fsm.add_transition(source="CekajPotez", dest="PropustiPotez")
        fsm.add_transition(source="PropustiPotez", dest="CekajPotez")
        self.add_behaviour(fsm)
     
 
class NadzornikIgre(Agent):
    class KonacniAutomat(FSMBehaviour):
        async def on_start(self):
            print("Nadzornik : spreman sam !")
            print("--------------------------------------------------------------------------")

    class PodjeliKarte(State):
        async def dajKarte(self, primatelj):
            global spilKarata
            karte = spilKarata[:5]
            spilKarata = spilKarata[5:]
            msg = Message(
                to=primatelj,
                body=f"{karte}"
                )
            await self.send(msg)
        
        async def staviPrvuKartu(self):
            global spilKarata
            global stol
            stol = spilKarata[:1]
            spilKarata = spilKarata[1:]

        async def run(self):
            global spilKarata
            random.shuffle(spilKarata)
            await self.dajKarte("primatelj@rec.foi.hr")
            await asyncio.sleep(1)
            await self.dajKarte("posiljatelj@rec.foi.hr")
            await self.staviPrvuKartu()

            self.set_next_state("ObradaZahtjeva")
            
    class ObradaZahtjeva(State):
        async def kontaktiraj(self, primatelj, info):
            msg = Message(
                to=primatelj,
                body=f"{info}"
                )
            await self.send(msg)

        async def promijesajKarte(self):
            global stol, spilKarata
            saStola = stol[:-1]
            stol = stol[-1:]
            spilKarata.extend(saStola)
            random.shuffle(spilKarata)

        async def run(self):
            msg = await self.receive(1000)
            if msg:
                if(msg.body == "MIJESAJ"):
                    await self.promijesajKarte()
                    print(f"Nadzornik : Promiješao sam karte")
                    await self.kontaktiraj(str(msg.sender), "NASTAVI")

            else:
                print("Nadzornik : Isteklo je vrijeme cekanja")
            print("--------------------------------------------------------------------------")
            self.set_next_state("ObradaZahtjeva")

    async def setup(self):
        fsm = self.KonacniAutomat()
        fsm.add_state(name="PodjeliKarte", state=self.PodjeliKarte(), initial=True)
        fsm.add_state(name="ObradaZahtjeva", state=self.ObradaZahtjeva())

        fsm.add_transition(source="PodjeliKarte", dest="ObradaZahtjeva")
        fsm.add_transition(source="ObradaZahtjeva", dest="ObradaZahtjeva")

        self.add_behaviour(fsm)
        

#===============MAIN=======================

igrac1 = Igrac("posiljatelj@rec.foi.hr", "tajna")
igrac1.postaviParametre("Igrac1" , "primatelj@rec.foi.hr", True)
igrac2 = Igrac("primatelj@rec.foi.hr", "tajna")
igrac2.postaviParametre("Igrac2" , "posiljatelj@rec.foi.hr", False)
nadzornik = NadzornikIgre("agent@rec.foi.hr", "tajna")

igrac1.start()
igrac2.start()
sleep(1)
nadzornik.start()

input("Za izlazak pritisnite ENTER\n--------------------------------------------------------------------------\n")

igrac2.stop()
igrac1.stop()
nadzornik.stop()

spade.quit_spade()
