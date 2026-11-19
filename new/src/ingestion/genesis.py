"""Authenticate the delegation and the three directly observed source sweeps, not actor identity."""
import argparse,json
import rlp
from eth_account import Account
from web3 import Web3
from src.ingestion.public_evidence import PublicEvidence
from src.visualization.common import ROOT

AUTH_TX='0xad99264d5532ae0dd04b2004eebda05f25657e70dacb764f7ac8d4ccd051298b'
VICTIM='0x28c6c06298d514db089934071355e5743bf21d60'


def recover_authority(auth):
    payload=rlp.encode([int(auth['chainId'],16),bytes.fromhex(auth['address'][2:]),int(auth['nonce'],16)])
    digest=Web3.keccak(b'\x05'+payload)
    return Account._recover_hash(digest,vrs=(int(auth['yParity'],16),int(auth['r'],16),int(auth['s'],16))).lower()


def run(online=False):
    p=PublicEvidence(ROOT,online);tx,tp=p.rpc('eth_getTransactionByHash',[AUTH_TX]);receipt,rp=p.rpc('eth_getTransactionReceipt',[AUTH_TX]);number=int(tx['blockNumber'],16)
    assert int(tx['type'],16)==4 and receipt['status']=='0x1'
    recovered=[{'nonce':int(a['nonce'],16),'delegate':a['address'].lower(),'chain_id':int(a['chainId'],16),'authority':recover_authority(a)} for a in tx['authorizationList']]
    assert len(recovered)==50 and {a['authority'] for a in recovered}=={VICTIM}
    delegates={a['delegate'] for a in recovered};assert len(delegates)==1
    codes={}
    for block in [number-1,number]:
        code,path=p.rpc('eth_getCode',[VICTIM,hex(block)]);codes[str(block)]={'code':code,'evidence':path}
    assert codes[str(number-1)]['code']=='0x'
    assert codes[str(number)]['code'].lower()=='0xef0100'+next(iter(delegates))[2:]
    doc,path=p.get('https://eips.ethereum.org/EIPS/eip-7702');assert doc.get('http_status')==200
    result={'authorization_tx':AUTH_TX,'operator_address':tx['from'].lower(),'authority':VICTIM,'delegate':next(iter(delegates)),'block':number,'transaction_index':int(tx['transactionIndex'],16),'authorization_count':len(recovered),'authorizations':recovered,'historical_code':codes,'evidence':{'transaction':tp,'receipt':rp,'eip7702':path},'observed_claim':'The 50 authorization signatures recover to the victim source address; successful type4 inclusion is accompanied by its historical delegation-code change.','interpretation_limits':['Proves signing/delegation capability, not how keys/signatures were obtained or legal identity.','Does not establish common beneficial control of all downstream recipients.','Block-end code shows delegation, not a full intrablock state proof.','Three observed sweep transactions and raw-unit asset inventory are reported separately.']}
    (ROOT/'data/processed/incident_delegation.json').write_text(json.dumps(result,indent=2));p.write_index();print('Recovered all50 EIP7702 authorities to source address; historical delegation code verified')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--online',action='store_true');a=p.parse_args();run(a.online)
