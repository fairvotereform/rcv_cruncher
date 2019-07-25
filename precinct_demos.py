from dbfread import DBF

def block_ethnicities(county, year, ethnicity):
    table = DBF('CVAPBLOCK/{}/{}_cvap_by_block.dbf'.format(year,ethnicity.replace(' ', '_')))
    return {row['BLOCK']:row['CVAP'] for row in table if row['BLOCK'][2:5] == county}

def precinct_percent_ethnicity():
    total = 0
    ethnic = 0

    year = '2014'
    county = '001'
    precinct = '510410'
    ethnicity = 'White Alone'
    ethnic_block_cvaps = block_ethnicities(county, year, ethnicity)
    total_block_cvaps = block_ethnicities(county, year, 'Total')
    precinct_block_fraction = 'blk2mprec/blk_mprec_{}_g{}_v01.txt'.format(county, year[-2:])
    with open(precinct_block_fraction) as f:
        for line in f:
            b, p, f = [i.strip('"') for i in line.strip('\n').split(',')]
            if precinct == p:
                ethnic += block_ethnicities(county, year, ethnicity)[b] * float(f)
                total += block_ethnicities(county, year, 'Total')[b] * float(f)

    return ethnic/total
                
                
            
            

if __name__ == "__main__":
    print(block_ethnicities('001', '2017', 'Total'))
    
