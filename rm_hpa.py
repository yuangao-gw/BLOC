#!/usr/bin/env python3

import os

DEP_DIR = "k8s_deployment/"

def delete_all_hpa():
    for name in os.listdir(DEP_DIR):
        cmd = f"kubectl delete hpa {name.split('.')[0]}"
        os.system(cmd)

if __name__ == "__main__":
    delete_all_hpa()
