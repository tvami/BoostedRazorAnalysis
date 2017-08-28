import re, os, sys, glob, time, logging, multiprocessing, socket, subprocess, shlex, getpass, ROOT
from optparse import OptionParser

# ---------------------- Cmd Line  -----------------------

# Read options from command line
usage = "Usage: python %prog filelists [options]"
parser = OptionParser(usage=usage)
parser.add_option("--run",         dest="run",         action="store_true", default=False,   help="Without this option, script only prints cmds it would otherwise excecute")
parser.add_option("--inputdir",    dest="INPUTDIR",     type="string",       default="",      help="Input directory (output of Analyzer)")
parser.add_option("--bin",         dest="BIN",          type="string",       default="",      help="Analysis bin, eg. _nj35 (default="")")
(opt,args) = parser.parse_args()

# ---------------------- Settings ------------------------

# List of input files
data = [
    "JetHT_Run2016B_03Feb2017_v2",
    "JetHT_Run2016C_03Feb2017",
    "JetHT_Run2016D_03Feb2017",
    "JetHT_Run2016E_03Feb2017",
    "JetHT_Run2016F_03Feb2017",
    "JetHT_Run2016G_03Feb2017",
    "JetHT_Run2016H_03Feb2017_v2",
    "JetHT_Run2016H_03Feb2017_v3"
]

signal = [
    "FastSim_SMS-T5ttcc",
    "FastSim_SMS-T5ttcc_mGluino1750to2300"
]

top = [
    # single top
    "ST_s-channel_4f_InclusiveDecays",
    "ST_t-channel_antitop_4f_inclusiveDecays",
    "ST_t-channel_top_4f_inclusiveDecays",
    "ST_tW_antitop_5f_inclusiveDecays",
    "ST_tW_top_5f_inclusiveDecays",
    # ttbar
    "TT_powheg-pythia8"
]
multijet = [
    "QCD_HT300to500",
    "QCD_HT500to700",
    "QCD_HT700to1000",
    "QCD_HT1000to1500",
    "QCD_HT1500to2000",
    "QCD_HT2000toInf",
    # V --> QQ
    "DYJetsToQQ_HT180",
    "WJetsToQQ_HT180",
    "ZJetsToQQ_HT600toInf",
    # VV --> QQQQ
    "WWTo4Q",
    "ZZTo4Q"
]
wjets = [
    "WJetsToLNu_Wpt-0To50",
    "WJetsToLNu_Wpt-100to200",
    "WJetsToLNu_Wpt-200toInf",
    "WJetsToLNu_Wpt-50To100"
]
ztoinv = [
    "ZJetsToNuNu_HT-1200To2500",
    "ZJetsToNuNu_HT-200To400",
    "ZJetsToNuNu_HT-2500ToInf",
    "ZJetsToNuNu_HT-400To600",
    "ZJetsToNuNu_HT-600To800",
    "ZJetsToNuNu_HT-800To1200"
]
other = [
    # g*/Z --> ll
    "DYJetsToLL_M-5to50_HT-100to200",
    "DYJetsToLL_M-5to50_HT-200to400",
    "DYJetsToLL_M-5to50_HT-400to600",
    "DYJetsToLL_M-5to50_HT-600toInf",
    "DYJetsToLL_M-50_HT-200to400",
    "DYJetsToLL_M-50_HT-2500toInf",
    "DYJetsToLL_M-50_HT-400to600",
    "DYJetsToLL_M-50_HT-600to800",
    "DYJetsToLL_M-50_HT-800to1200",
    "DYJetsToLL_M-50_HT-1200to2500",
    # gamma
    "GJets_HT-40To100",
    "GJets_HT-100To200",
    "GJets_HT-200To400",
    "GJets_HT-400To600",
    "GJets_HT-600ToInf",
    # ttbar + X
    "TTGJets",
    "TTWJetsToLNu",
    "TTWJetsToQQ",
    "TTZToLLNuNu",
    "TTZToQQ",
    "TTTT",
    # VV
    "WWTo2L2Nu",
    "WWToLNuQQ",
    "WZTo1L1Nu2Q",
    "WZTo1L3Nu",
    "WZTo2L2Q",
    "WZTo2Q2Nu",
    "WZTo3LNu",
    "ZZTo2L2Nu",
    "ZZTo2L2Q",
    "ZZTo2Q2Nu",
    "ZZTo4L",
    # VVV
    "WWW",
    "WWZ",
    "WZZ",
    "ZZZ"
]

# List of systematics to consider
systematics = [
    "",
#    "_lumiUp",
#    "_lumiDown",
    "_pileupUp",
    "_pileupDown",
    "_alphasUp",
    "_alphasDown",
    "_facscaleUp",
    "_facscaleDown",
    "_renscaleUp",
    "_renscaleDown",
    "_facrenscaleUp", 
    "_facrenscaleDown", 
    "_triggerUp",
    "_triggerDown",
    "_jesUp",
    "_jesDown",
    "_jerUp",
    "_jerDown",
    "_metUp", 
    "_metDown", 
    "_elerecoUp",
    "_elerecoDown",
    "_eleidUp",
    "_eleidDown",
    "_eleisoUp",
    "_eleisoDown",
    "_elefastsimUp",
    "_elefastsimDown",
    "_muontrkUp",
    "_muontrkDown",
    "_muonidisoUp",
    "_muonidisoDown",
    "_muonfastsimUp",
    "_muonfastsimDown",
    "_btagUp",
    "_btagDown",
    "_btagfastsimUp",
    "_btagfastsimDown",
    "_wtagUp",
    "_wtagDown",
    "_wtagfastsimUp",
    "_wtagfastsimDown",
    "_toptagUp",
    "_toptagDown",
    "_toptagfastsimUp",
    "_toptagfastsimDown",
]

# --------------------- Functions ------------------------
# Show and run command with stdout on screen
icommand=0
def special_call(cmd, verbose=1):
    global icommand, opt
    if verbose:
        if opt.run:
            print("[%d]" % icommand),
        else:
            print("[dry]"),
        for i in xrange(len(cmd)): print cmd[i],
        print ""
    if opt.run:
        ntry = 0
        while True:
            try:
                if subprocess.call(cmd):
                    print "ERROR: Problem executing command:"
                    print("[%d]" % icommand)
                    for i in xrange(len(cmd)): print cmd[i],
                    print ""
                    print "exiting."
                    sys.exit()
            except:
                print "Could not excecute command: "
                print("[%d]" % icommand)
                for i in xrange(len(cmd)): print cmd[i],
                print ""
                print "Wait 10s and continue"
                time.sleep(10)
                ntry += 1
                if ntry == 20: sys.exit()
                continue
            break
        if verbose: print ""
    sys.stdout.flush()
    icommand+=1

# Run command with stdout/stderr saved to logfile
def logged_call(cmd, logfile):
    global opt
    dirname = os.path.dirname(logfile)
    if dirname != "" and not os.path.exists(dirname):
        special_call(["mkdir", "-p", os.path.dirname(logfile)], 0)
    if opt.run:
        ntry = 0
        while True:
            try:
                with open(logfile, "a") as log:
                    proc = subprocess.Popen(cmd, stdout=log, stderr=log, close_fds=True)
                    proc.wait()
            except:
                print "Could not write to disk (IOError), wait 10s and continue"
                time.sleep(10)
                ntry += 1
                if ntry == 20: sys.exit()
                continue
            break
    else:
        proc = subprocess.call(["echo", "[dry]"]+cmd+[">", logfile])

def load(f, name, pf=""):
    h = f.Get(name)
    h_new = ROOT.TH1D(h.GetName()+pf,h.GetTitle(),h.GetNbinsX(),h.GetXaxis().GetXmin(),h.GetXaxis().GetXmax())
    for i in range (0, h.GetNbinsX()+2):
        h_new.SetBinContent(i,h.GetBinContent(i));
        h_new.SetBinError(i,h.GetBinError(i));
    h_new.SetEntries(h.GetEntries())
    h_new.SetDirectory(0)
    return h_new

def bg_est(name, data, sub, mult, div):
    est = data.Clone(name)
    for hist in sub:
        est.Add(hist, -1)
    est.Multiply(mult)
    est.Divide(div)
    return est
    
# ----------------- Merge histograms --------------------

print "Merging histograms from directory: "+opt.INPUTDIR

data_files = []
for name in data: data_files.append(opt.INPUTDIR+"/hadd/"+name+".root")

signal_files = []
for name in signal: signal_files.append(opt.INPUTDIR+"/hadd/"+name+".root")

data_files = []
for name in data: data_files.append(opt.INPUTDIR+"/hadd/"+name+".root")
signal_files = []
for name in signal: signal_files.append(opt.INPUTDIR+"/hadd/"+name+".root")
multijet_files = []
for name in multijet: multijet_files.append(opt.INPUTDIR+"/hadd/"+name+".root")
top_files = []
for name in top: top_files.append(opt.INPUTDIR+"/hadd/"+name+".root")
wjets_files = []
for name in wjets: wjets_files.append(opt.INPUTDIR+"/hadd/"+name+".root")
ztoinv_files = []
for name in ztoinv: ztoinv_files.append(opt.INPUTDIR+"/hadd/"+name+".root")
other_files = []
for name in other: other_files.append(opt.INPUTDIR+"/hadd/"+name+".root")

logged_call(["hadd", "-f", "-v", "syst_"+opt.INPUTDIR+"/hadd/data.root"]+data_files,         "syst_"+opt.INPUTDIR+"/hadd/log/data.log")
logged_call(["hadd", "-f", "-v", "syst_"+opt.INPUTDIR+"/hadd/signal.root"]+signal_files,     "syst_"+opt.INPUTDIR+"/hadd/log/signal.log")
logged_call(["hadd", "-f", "-v", "syst_"+opt.INPUTDIR+"/hadd/multijet.root"]+multijet_files, "syst_"+opt.INPUTDIR+"/hadd/log/multijet.log")
logged_call(["hadd", "-f", "-v", "syst_"+opt.INPUTDIR+"/hadd/top.root"]+top_files,           "syst_"+opt.INPUTDIR+"/hadd/log/top.log")
logged_call(["hadd", "-f", "-v", "syst_"+opt.INPUTDIR+"/hadd/wjets.root"]+wjets_files,       "syst_"+opt.INPUTDIR+"/hadd/log/wjets.log")
logged_call(["hadd", "-f", "-v", "syst_"+opt.INPUTDIR+"/hadd/ztoinv.root"]+ztoinv_files,     "syst_"+opt.INPUTDIR+"/hadd/log/ztoinv.log")
logged_call(["hadd", "-f", "-v", "syst_"+opt.INPUTDIR+"/hadd/other.root"]+other_files,       "syst_"+opt.INPUTDIR+"/hadd/log/other.log")

# ----------------- Harvest histograms -------------------

# Load:
# Q_data, Q_TT, Q_MJ, Q_WJ, Q_ZI, Q_OT
# W_data, W_TT, W_MJ, W_WJ, W_ZI, W_OT
# T_data, T_TT, T_MJ, T_WJ, T_ZI, T_OT
# S_data, S_TT, S_MJ, S_WJ, S_ZI, S_OT

print "Loading histograms"


# Data
f = ROOT.TFile.Open("syst_"+opt.INPUTDIR+"/hadd/data.root")
Q_data = load(f,"MRR2_Q_data"+opt.BIN,"_data")
W_data = load(f,"MRR2_W_data"+opt.BIN,"_data")
T_data = load(f,"MRR2_T_data"+opt.BIN,"_data")
S_data = load(f,"MRR2_S_data"+opt.BIN,"_data")

# Signal
f = ROOT.TFile.Open("syst_"+opt.INPUTDIR+"/hadd/signal.root")
S_signal = []
counter = 0
for ikey in range(0, f.GetListOfKeys().GetEntries()):
    name = f.GetListOfKeys().At(ikey).GetName()
    if name.startswith("MRR2_S_signal") and not "Up" in name and not "Down" in name:
        if not "_nj35" in name and not "_nj6" in name:
            counter+=1
            S_syst = []
            for syst in systematics:
                S_syst.append(load(f, name+opt.BIN+syst, "_sig"))
            S_signal.append(S_syst)
    #if counter>10:
    #    break

# Background
# top
f = ROOT.TFile.Open("syst_"+opt.INPUTDIR+"/hadd/top.root")
Q_TT = []
W_TT = []
T_TT = []
S_TT = []
for syst in systematics:
    Q_TT.append(load(f,"MRR2_Q_bkg"+opt.BIN+syst,"_TT"))
    W_TT.append(load(f,"MRR2_W_bkg"+opt.BIN+syst,"_TT"))
    T_TT.append(load(f,"MRR2_T_bkg"+opt.BIN+syst,"_TT"))
    S_TT.append(load(f,"MRR2_S_bkg"+opt.BIN+syst,"_TT"))
# multijet
f = ROOT.TFile.Open("syst_"+opt.INPUTDIR+"/hadd/multijet.root")
Q_MJ = []
W_MJ = []
T_MJ = []
S_MJ = []
for syst in systematics:
    Q_MJ.append(load(f,"MRR2_Q_bkg"+opt.BIN+syst,"_MJ"))
    W_MJ.append(load(f,"MRR2_W_bkg"+opt.BIN+syst,"_MJ"))
    T_MJ.append(load(f,"MRR2_T_bkg"+opt.BIN+syst,"_MJ"))
    S_MJ.append(load(f,"MRR2_S_bkg"+opt.BIN+syst,"_MJ"))
# wjets
f = ROOT.TFile.Open("syst_"+opt.INPUTDIR+"/hadd/wjets.root")
Q_WJ = []
W_WJ = []
T_WJ = []
S_WJ = []
for syst in systematics:
    Q_WJ.append(load(f,"MRR2_Q_bkg"+opt.BIN+syst,"_WJ"))
    W_WJ.append(load(f,"MRR2_W_bkg"+opt.BIN+syst,"_WJ"))
    T_WJ.append(load(f,"MRR2_T_bkg"+opt.BIN+syst,"_WJ"))
    S_WJ.append(load(f,"MRR2_S_bkg"+opt.BIN+syst,"_WJ"))
# ztoinv
f = ROOT.TFile.Open("syst_"+opt.INPUTDIR+"/hadd/ztoinv.root")
Q_ZI = []
W_ZI = []
T_ZI = []
S_ZI = []
for syst in systematics:
    Q_ZI.append(load(f,"MRR2_Q_bkg"+opt.BIN+syst,"_ZI"))
    W_ZI.append(load(f,"MRR2_W_bkg"+opt.BIN+syst,"_ZI"))
    T_ZI.append(load(f,"MRR2_T_bkg"+opt.BIN+syst,"_ZI"))
    S_ZI.append(load(f,"MRR2_S_bkg"+opt.BIN+syst,"_ZI"))
# other
f = ROOT.TFile.Open("syst_"+opt.INPUTDIR+"/hadd/other.root")
Q_OT = []
W_OT = []
T_OT = []
S_OT = []
for syst in systematics:
    Q_OT.append(load(f,"MRR2_Q_bkg"+opt.BIN+syst,"_OT"))
    W_OT.append(load(f,"MRR2_W_bkg"+opt.BIN+syst,"_OT"))
    T_OT.append(load(f,"MRR2_T_bkg"+opt.BIN+syst,"_OT"))
    S_OT.append(load(f,"MRR2_S_bkg"+opt.BIN+syst,"_OT"))


# --------------- Background Estimation ------------------

# Formulas for bkg estimate:
# S_MJ_est = (Q_data - Q_notMJ) * S_MJ / Q_MJ
# T_MJ_est = (Q_data - Q_notMJ) * T_MJ / Q_MJ
# S_WJ_est = (W_data - W_notWJ) * S_WJ / W_WJ
# S_TT_est = (T_data - T_MJ_est - T_notTTorMJ) * S_TT / T_TT

# Estimate:
#T_MJ_est = (Q_data - Q_TT     - Q_WJ - Q_ZI - Q_OT) * T_MJ / Q_MJ
#S_MJ_est = (Q_data - Q_TT     - Q_WJ - Q_ZI - Q_OT) * S_MJ / Q_MJ
#S_WJ_est = (W_data - W_TT     - W_MJ - W_ZI - W_OT) * S_WJ / W_WJ
#S_TT_est = (T_data - T_MJ_est - T_WJ - T_ZI - T_OT) * S_TT / T_TT
#S_ZI_est = S_ZI
#S_OT_est = S_OT
#S_est    = S_MJ_est + S_WJ_est + S_TT_est + S_ZI_est + S_OT_est

# Caluclating background estimates
print "Calculating background estimates"

Top_est      = []
MultiJet_est = []
WJets_est    = []
ZInv_est     = []
Other_est    = []
for i in range(0, len(systematics)):
    T_MJ_est = bg_est("Top_MJ_est",                  Q_data, [Q_TT[i],            Q_WJ[i], Q_ZI[i], Q_OT[i]], T_MJ[i], Q_MJ[i])
    S_TT_est = bg_est("Top"         +systematics[i], T_data, [          T_MJ_est, T_WJ[i], T_ZI[i], T_OT[i]], S_TT[i], T_TT[i])
    S_MJ_est = bg_est("MultiJet"    +systematics[i], Q_data, [Q_TT[i],            Q_WJ[i], Q_ZI[i], Q_OT[i]], S_MJ[i], Q_MJ[i])
    S_WJ_est = bg_est("WJets"       +systematics[i], W_data, [W_TT[i],  W_MJ[i],           W_ZI[i], W_OT[i]], S_WJ[i], W_WJ[i])
    S_ZI_est = S_ZI[i].Clone("ZInv" +systematics[i])
    S_OT_est = S_OT[i].Clone("Other"+systematics[i])
    Top_est     .append(S_TT_est)
    MultiJet_est.append(S_MJ_est)
    WJets_est   .append(S_WJ_est)
    ZInv_est    .append(S_ZI_est)
    Other_est   .append(S_OT_est)

# Now save a different root file for each signal point
print "Looping on Signal points"

for signal_syst in S_signal:
    scan_point = signal_syst[0].GetName()[:-4].replace("MRR2_S_signal_","")
    filename = "syst_"+opt.INPUTDIR+"/RazorBoost_lumi-35.9_WAna"+opt.BIN+"_T5ttcc_"+scan_point+".root"
    fout = ROOT.TFile.Open(filename,"recreate")
    print " - Creating root file: "+filename
    # Add signal systematics
    for i in range(0, len(systematics)):
        signal_syst[i].Write("Signal"+systematics[i])
    # Add background estimates
    for bkg in [Top_est, MultiJet_est, WJets_est, ZInv_est, Other_est]:
        for syst_var in bkg:
            syst_var.Write()
    # Add data counts
    S_data.Write("data_obs")

print "Done."
