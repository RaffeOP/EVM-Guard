pragma solidity 0.5.12;

contract Safe7364 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public shares;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        reserve += msg.value;
    }

    function totalDeposits() public view returns (uint256) { return reserve; }

    function ownerOf_() public view returns (address) { return owner; }
}
