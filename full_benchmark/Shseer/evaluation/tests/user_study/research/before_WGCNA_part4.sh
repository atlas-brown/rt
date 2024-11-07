#!/bin/bash

module load R/3.6.1

Help(){
  echo ""
  echo "Usage: ./WGCNA_part4.sh -o [PATH of network.Rdata] -m [Module] -t [Trait] -i [GeneID type]"
  echo ""
	echo "--------------------- $(tput bold)WGCNA_part4$(tput sgr0) -------------------------------"
	echo "This part will: "
	echo "1. Calculate ModuleMembership of all the genes in the selected module"
	echo "2. Calculate gene significance for the selected trait of all the genes in the selected module"
	echo "3. Perform GO enrichment analysis of the selected module"
	echo "4. Perform KEGG pathway analysis of gene in the selected module"
	echo ""
	echo "--------------------- $(tput bold)Data$(tput sgr0)---------------------------------------"
	echo "$(tput bold)Input data$(tput sgr0)"
	echo "network.Rdata (returned by WGCNA_part3)"
	echo ""
	echo "$(tput bold)Output data$(tput sgr0)"
	echo "Part4_eigengeneTraitDendrogram.pdf      Dendrogram and correlation heatmap of selected trait and module eigengenes"
	echo "Part4_geneInModule_color.pdf            Module membership v.s gene significance of genes in the selected module"
	echo "geneInModule_color_trait.tsv            Annotation of genes in the selected module "
	echo ""
	echo "--------------------- $(tput bold)Parameters$(tput sgr0) --------------------------------" 
	echo "-o|--output      directory of output (folder of network.Rdata)"
	echo "-m|--module      color of the selected module"
	echo "-t|--trait       name of the selected trait"
	echo "-i|--id          type of GeneID used in the expression data"
	echo "$(tput bold)GeneID OPTIONS$(tput sgr0):"
	echo "        [1]: ensembl_gene_id"
	echo "        [2]: ensembl_gene_id_version"
	echo "        [3]: hgnc_symbol"
	
	echo ""
}


while [[ $# -gt 0 ]]
do
    key="${1}"
    case ${key} in
    -o|--output)
	OUTPUT="${2}"
	shift
	shift
	;;
    -m|--module)
        MODULE="${2}"
        shift # past argument
        shift # past value
        ;;
    -t|--trait)
        TRAIT="${2}"
        shift # past argument
        shift # past value
        ;;
    -i|--id)
        GENEID="${2}"
        shift # past argument
        shift # past value
        ;;
    -h|--help)
        Help
        exit 1
        ;;
    *)    # unknown option
        shift # past argument
        ;;
    esac
done


# check parameters
if [ -z "$OUTPUT" ] ; then
	echo -e "$(tput setaf 1)NO output path supplied!\n$(tput sgr 0)Please enter the directory of network.RData! (i.e. -o [path])"
	exit 1
fi

if [ -z "$MODULE" ] ; then  
	echo -e "$(tput setaf 1)NO module selected!\n$(tput sgr 0)Please entre the color of the module of interest! (i.e. -m [color])"
	exit 1
fi

if [ -z "$TRAIT" ] ; then  
	echo -e "$(tput setaf 1)NO trait selected!\n$(tput sgr 0)Please entre the name of the trait of interest! (i.e. -t [trait])"
	exit 1
fi

if [ -z "$GENEID" ] || [ "$GENEID" -gt 3 ] || [ "$GENEID" -lt 1 ]; then  
	echo -e "$(tput setaf 1)NO Gene ID type supplied!\n$(tput sgr 0)Please entre the type GeneID of expression data! (i.e. -i [1])"
	echo "        [1]: ensembl_gene_id"
	echo "        [2]: ensembl_gene_id_version"
	echo "        [3]: hgnc_symbol"
	exit 1
fi


# run R
Rscript WGCNA_part4.R $OUTPUT $GENEID $MODULE $TRAIT 
