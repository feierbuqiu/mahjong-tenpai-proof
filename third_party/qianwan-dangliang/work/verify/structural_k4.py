#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""structural_k4.py <plan_k4.json> -- k=4 结构复核 (structural_k3 的 k=4 包装)."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0]] + (sys.argv[1:] or ["work/recon/plan_k4_lead.json"])
exec(open(os.path.join(HERE, "structural_k3.py"), encoding="utf-8").read())
