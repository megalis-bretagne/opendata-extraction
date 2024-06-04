<?xml version="1.0" encoding="UTF-8"?>
<!--
Transform TOTEM xml file into CSV like XML file following SCDL Budget schema

TOTEM: http://odm-budgetaire.org/
Budget schema: https://git.opendatafrance.net/scdl/budget

author: Pierre Dittgen, Jailbreak Paris
pierre.dittgen@jailbreak.paris
-->
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:totem="http://www.minefi.gouv.fr/cp/demat/docbudgetaire">
    <xsl:output method="xml" encoding="utf-8" />

    <xsl:param name="plandecompte" />

    <!-- plandecompte path is given as parameter now -->
    <xsl:variable name="plan_de_compte" select="document($plandecompte)" />

    <xsl:template match="/">
        
        <xsl:variable name="NatDec">
            <xsl:variable name="code" select="//totem:BlocBudget/totem:NatDec/@V" />
            <!-- DecNat labels from CommunBudget.xsd -->
            <xsl:choose>
                <xsl:when test="$code = '01'">budget primitif</xsl:when>
                <xsl:when test="$code = '02'">décision modificative</xsl:when>
                <xsl:when test="$code = '03'">budget supplémentaire</xsl:when>
                <xsl:when test="$code = '09'">compte administratif</xsl:when>
                <xsl:when test="$code = '10'">Compte administratif</xsl:when>
                <xsl:otherwise>NatDec inconnu: <xsl:value-of select="$code"/></xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="Exer" select="//totem:BlocBudget/totem:Exer/@V" />
        <xsl:variable name="IdEtab" select="//totem:EnTeteBudget/totem:IdEtab/@V" />
<!--        <xsl:variable name="LibelleColl" select="//totem:EnTeteDocBudgetaire/totem:LibelleColl/@V" />-->
        <xsl:variable name="LibelleEtab" select="//totem:EnTeteBudget/totem:LibelleEtab/@V" />
        <csv>
            <header>
                <column name="BGT_NATDEC"/>
                <column name="BGT_ANNEE"/>
                <column name="BGT_SIRET"/>
                <column name="BGT_NOM"/>
                <column name="BGT_CONTNAT"/>
                <column name="BGT_CONTNAT_LABEL"/>
                <column name="BGT_NATURE"/>
                <column name="BGT_NATURE_LABEL"/>
                <column name="BGT_FONCTION"/>
                <column name="BGT_FONCTION_LABEL"/>
                <column name="BGT_OPERATION"/>
                <column name="BGT_SECTION"/>
                <column name="BGT_OPBUDG"/>
                <column name="BGT_CODRD"/>
                <column name="BGT_MTREAL"/>
                <column name="BGT_MTBUDGPREC"/>
                <column name="BGT_MTRARPREC"/>
                <column name="BGT_MTPROPNOUV"/>
                <column name="BGT_MTPREV"/>
                <column name="BGT_CREDOUV"/>
                <column name="BGT_MTRAR3112"/>
                <column name="BGT_ARTSPE"/>
            </header>
            <data>
                <xsl:for-each select=".//totem:LigneBudget[@calculated='false' or not (@calculated)]">
                    <row lineno="{position()}">

                        <xsl:variable name="contNat" select="totem:ContNat/@V" />
                        <xsl:variable name="chapitre" select="$plan_de_compte/Nomenclature/Nature/Chapitres/Chapitre[@Code=$contNat]" />
                        <xsl:variable name="nature" select="totem:Nature/@V" />
                        <xsl:variable name="fonction" select="totem:Fonction/@V" />

                        <cell name="BGT_NATDEC" value="{$NatDec}" />
                        <cell name="BGT_ANNEE" value="{$Exer}" />
                        <cell name="BGT_SIRET" value="{$IdEtab}" />
                        <cell name="BGT_NOM" value="{$LibelleEtab}" />
                        <cell name="BGT_CONTNAT" value="{$contNat}" />
                        <cell name="BGT_CONTNAT_LABEL">
                            <xsl:attribute name="value">
                                <xsl:value-of select="$chapitre/@Libelle" />
                            </xsl:attribute>
                        </cell>
                        <cell name="BGT_NATURE" value="{$nature}" />
                        <cell name="BGT_NATURE_LABEL">
                            <xsl:attribute name="value">
                                <xsl:value-of select="$plan_de_compte/Nomenclature/Nature/Comptes//Compte[@Code=$nature]/@Libelle" />
                            </xsl:attribute>
                        </cell>
                        <cell name="BGT_FONCTION" value="{$fonction}" />
                        <cell name="BGT_FONCTION_LABEL">
                            <xsl:attribute name="value">
                                <xsl:value-of select="$plan_de_compte/Nomenclature/Fonction/RefFonctionnelles//RefFonc[@Code=$fonction]/@Libelle" />
                            </xsl:attribute>
                        </cell>
                        <cell name="BGT_OPERATION">
                            <xsl:attribute name="value">
                                <xsl:if test="totem:Operation">
                                    <xsl:value-of select="totem:Operation/@V"/>
                                </xsl:if>
                            </xsl:attribute>
                        </cell>
                        <cell name="BGT_SECTION">
                            <xsl:variable name="code" select="totem:CaracSup/@V" />
                            <xsl:attribute name="value">
                                <xsl:if test="$code = 'I'">investissement</xsl:if>
                                <xsl:if test="$code = 'F'">fonctionnement</xsl:if>
                            </xsl:attribute>
                        </cell>
<!--                        <cell name="BGT_SECTION">-->
<!--                            <xsl:variable name="section" select="$chapitre/@Section" />-->
<!--                            <xsl:attribute name="value">-->
<!--                                <xsl:if test="$section = 'I'">investissement</xsl:if>-->
<!--                                <xsl:if test="$section = 'F'">fonctionnement</xsl:if>-->
<!--                            </xsl:attribute>-->
<!--                        </cell>-->
                        <cell name="BGT_OPBUDG">
                            <xsl:variable name="code" select="totem:OpBudg/@V" />
                            <xsl:attribute name="value">
                                <xsl:if test="$code = '0'">réel</xsl:if>
                                <xsl:if test="$code = '1'">ordre</xsl:if>
                            </xsl:attribute>
                        </cell>
                        <cell name="BGT_CODRD">
                            <xsl:variable name="code" select="totem:CodRD/@V" />
                            <xsl:attribute name="value">
                                <xsl:if test="$code = 'R'">recette</xsl:if>
                                <xsl:if test="$code = 'D'">dépense</xsl:if>
                            </xsl:attribute>
                        </cell>
                        <cell name="BGT_MTREAL" value="{totem:MtReal/@V}"/>
                        <cell name="BGT_MTBUDGPREC" value="{totem:MtBudgPrec/@V}"/>
                        <cell name="BGT_MTRARPREC" value="{totem:MtRARPrec/@V}"/>
                        <cell name="BGT_MTPROPNOUV" value="{totem:MtPropNouv/@V}"/>
                        <cell name="BGT_MTPREV" value="{totem:MtPrev/@V}"/>
                        <cell name="BGT_CREDOUV" value="{totem:CredOuv/@V}"/>
                        <cell name="BGT_MTRAR3112" value="{totem:MtRAR3112/@V}"/>
                        <cell name="BGT_ARTSPE">
                            <xsl:variable name="artSpe" select="totem:ArtSpe/@V"/>
                            <xsl:attribute name="value">
                                <xsl:if test="$artSpe = 'false'">non spécialisé</xsl:if>
                                <xsl:if test="$artSpe = 'true'">spécialisé</xsl:if>
                            </xsl:attribute>
                        </cell>
                    </row>
                </xsl:for-each>
            </data>
        </csv>
    </xsl:template>

    <xsl:template match="totem:LigneBudget">
        <xsl:copy-of select="."/>
    </xsl:template>

</xsl:stylesheet>