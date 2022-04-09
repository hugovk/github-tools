"""
Given a list of BPO issues and open PRs, containing some false positives,
check which PRs are really still open using the GitHub API.
"""
import os

from github import Github

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

# https://dpaste.com/AF2DKJG8B
bpo_to_prs = """
https://bugs.python.org/issue39791: 23715
https://bugs.python.org/issue40269: 19593
https://bugs.python.org/issue34008: 8023
https://bugs.python.org/issue23878: 15555
https://bugs.python.org/issue42817: 24075
https://bugs.python.org/issue36682: 12896
https://bugs.python.org/issue34001: 8055
https://bugs.python.org/issue45747: 32299
https://bugs.python.org/issue26828: 14432
https://bugs.python.org/issue26470: 12694
https://bugs.python.org/issue16270: 13951
https://bugs.python.org/issue35780: 11733, 11733, 11733
https://bugs.python.org/issue36346: 12409
https://bugs.python.org/issue21161: 15194
https://bugs.python.org/issue34397: 8757
https://bugs.python.org/issue37366: 14419
https://bugs.python.org/issue38692: 25515
https://bugs.python.org/issue36570: 12740
https://bugs.python.org/issue33136: 6229
https://bugs.python.org/issue36161: 16599
https://bugs.python.org/issue9566: 11010
https://bugs.python.org/issue38894: 23025
https://bugs.python.org/issue29743: 10029
https://bugs.python.org/issue33741: 8938
https://bugs.python.org/issue1539381: 8451
https://bugs.python.org/issue41379: 27830
https://bugs.python.org/issue31752: 10040
https://bugs.python.org/issue45186: 28379
https://bugs.python.org/issue27484: 27959
https://bugs.python.org/issue32309: 4848
https://bugs.python.org/issue1635741: 22242, 23091, 23188, 23304, 23535
https://bugs.python.org/issue40421: 32417
https://bugs.python.org/issue44195: 26272
https://bugs.python.org/issue22928: 15299
https://bugs.python.org/issue35431: 13731
https://bugs.python.org/issue41914: 28564
https://bugs.python.org/issue24665: 28136
https://bugs.python.org/issue31664: 26526
https://bugs.python.org/issue43669: 28602
https://bugs.python.org/issue30693: 31713
https://bugs.python.org/issue37629: 15955
https://bugs.python.org/issue34317: 8622
https://bugs.python.org/issue4489: 22968
https://bugs.python.org/issue45763: 32299
https://bugs.python.org/issue41134: 14464
https://bugs.python.org/issue32314: 5262
https://bugs.python.org/issue29312: 14589
https://bugs.python.org/issue42917: 32055
https://bugs.python.org/issue31404: 3606
https://bugs.python.org/issue34434: 29976
https://bugs.python.org/issue33376: 10250
https://bugs.python.org/issue4225: 23143
https://bugs.python.org/issue38076: 18038
https://bugs.python.org/issue22640: 17134
https://bugs.python.org/issue34788: 25824
https://bugs.python.org/issue45516: 29174
https://bugs.python.org/issue44278: 26477
https://bugs.python.org/issue14191: 24367
https://bugs.python.org/issue33393: 29783
https://bugs.python.org/issue36452: 12619
https://bugs.python.org/issue25198: 6665
https://bugs.python.org/issue31903: 9215
https://bugs.python.org/issue40334: 19969
https://bugs.python.org/issue33159: 6271
https://bugs.python.org/issue40167: 19326
https://bugs.python.org/issue44399: 27350
https://bugs.python.org/issue29521: 146
https://bugs.python.org/issue32810: 11166
https://bugs.python.org/issue33402: 6678
https://bugs.python.org/issue38326: 16496
https://bugs.python.org/issue35598: 11427
https://bugs.python.org/issue31310: 5172
https://bugs.python.org/issue30178: 1572
https://bugs.python.org/issue35617: 11364, 11364, 11364
https://bugs.python.org/issue46712: 31596, 32152
https://bugs.python.org/issue35263: 10564
https://bugs.python.org/issue11555: 11565, 11565, 11565, 11565
https://bugs.python.org/issue24568: 9938
https://bugs.python.org/issue31084: 31355
https://bugs.python.org/issue32367: 8802
https://bugs.python.org/issue3264: 5267
https://bugs.python.org/issue4111: 25115
https://bugs.python.org/issue31878: 4145
https://bugs.python.org/issue39682: 30971
https://bugs.python.org/issue39924: 18998
https://bugs.python.org/issue39925: 18909
https://bugs.python.org/issue34744: 9427
https://bugs.python.org/issue46014: 32282
https://bugs.python.org/issue29532: 209
https://bugs.python.org/issue39609: 18458
https://bugs.python.org/issue32960: 5920
https://bugs.python.org/issue32250: 4766
https://bugs.python.org/issue8814: 21392
https://bugs.python.org/issue27313: 29425
https://bugs.python.org/issue31178: 3897
https://bugs.python.org/issue39491: 18422
https://bugs.python.org/issue34187: 9922
https://bugs.python.org/issue31875: 4458
https://bugs.python.org/issue10141: 23794
https://bugs.python.org/issue17636: 18347
https://bugs.python.org/issue40260: 19549
https://bugs.python.org/issue3753: 15072
https://bugs.python.org/issue44797: 27512
https://bugs.python.org/issue32663: 8470
https://bugs.python.org/issue24120: 23025
https://bugs.python.org/issue41283: 21573
https://bugs.python.org/issue33975: 7951, 7952
https://bugs.python.org/issue42834: 26161
https://bugs.python.org/issue15248: 11934
https://bugs.python.org/issue39995: 19788
https://bugs.python.org/issue29549: 204
https://bugs.python.org/issue29548: 87
https://bugs.python.org/issue33079: 6240
https://bugs.python.org/issue40465: 31818
https://bugs.python.org/issue40725: 21169
https://bugs.python.org/issue42128: 27384
https://bugs.python.org/issue28889: 1589
https://bugs.python.org/issue36924: 13340
https://bugs.python.org/issue37322: 25572
https://bugs.python.org/issue46415: 30642
https://bugs.python.org/issue40466: 19858
https://bugs.python.org/issue21222: 21304
https://bugs.python.org/issue41045: 21552
https://bugs.python.org/issue25658: 4060
https://bugs.python.org/issue35367: 11143
https://bugs.python.org/issue38914: 23264
https://bugs.python.org/issue33518: 6936
https://bugs.python.org/issue45865: 29698
https://bugs.python.org/issue35579: 11323
https://bugs.python.org/issue4379: 25307, 25308
https://bugs.python.org/issue19903: 2822
https://bugs.python.org/issue42792: 26373
https://bugs.python.org/issue22533: 20339
https://bugs.python.org/issue42247: 23688
https://bugs.python.org/issue39985: 19065
https://bugs.python.org/issue46576: 32382
https://bugs.python.org/issue36835: 13159
https://bugs.python.org/issue30477: 1820
https://bugs.python.org/issue34219: 8458
https://bugs.python.org/issue42071: 22751
https://bugs.python.org/issue36422: 14292
https://bugs.python.org/issue32903: 5946
https://bugs.python.org/issue32609: 5259
https://bugs.python.org/issue41511: 21799
https://bugs.python.org/issue40174: 19385
https://bugs.python.org/issue46440: 30832
https://bugs.python.org/issue36995: 13464
https://bugs.python.org/issue40361: 19649
https://bugs.python.org/issue35482: 11224
https://bugs.python.org/issue32294: 4887
https://bugs.python.org/issue45274: 31290
https://bugs.python.org/issue40670: 20830
https://bugs.python.org/issue43218: 24530
https://bugs.python.org/issue22295: 24003
https://bugs.python.org/issue7105: 20687
https://bugs.python.org/issue40185: 31779
https://bugs.python.org/issue27100: 17609
https://bugs.python.org/issue28764: 23553
https://bugs.python.org/issue37776: 17575
https://bugs.python.org/issue36643: 27330
https://bugs.python.org/issue1754: 2413
https://bugs.python.org/issue35770: 11615
https://bugs.python.org/issue45711: 30289
https://bugs.python.org/issue31699: 4256
https://bugs.python.org/issue35152: 10305
https://bugs.python.org/issue47190: 32293
https://bugs.python.org/issue45636: 30073
https://bugs.python.org/issue39298: 31686
https://bugs.python.org/issue34547: 9713
https://bugs.python.org/issue33885: 7886
https://bugs.python.org/issue44946: 30044
https://bugs.python.org/issue39640: 18516
https://bugs.python.org/issue43762: 25778
https://bugs.python.org/issue42892: 24192
https://bugs.python.org/issue43086: 27249
https://bugs.python.org/issue37435: 14432
https://bugs.python.org/issue36674: 13180
https://bugs.python.org/issue39881: 18817
https://bugs.python.org/issue32394: 5910
https://bugs.python.org/issue39774: 18677
https://bugs.python.org/issue39355: 32175
https://bugs.python.org/issue39761: 18672
https://bugs.python.org/issue41443: 23886
https://bugs.python.org/issue19438: 22161
https://bugs.python.org/issue12169: 12169
https://bugs.python.org/issue46590: 31020
https://bugs.python.org/issue42673: 23833
"""


g = Github(GITHUB_TOKEN, per_page=100)
repo = g.get_repo("python/cpython")


for line in bpo_to_prs.strip().splitlines():
    bpo_url, pr_numbers = line.split(": ")
    for pr_number in pr_numbers.split(", "):
        pr = repo.get_pull(int(pr_number))
        # Still open
        if not pr.closed_at:
            print(f"{bpo_url}\t{pr.html_url}\t{pr.title}")
