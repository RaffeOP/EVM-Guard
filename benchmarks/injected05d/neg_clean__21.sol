pragma solidity 0.5.12;

contract Ledger6131 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public shares;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        reserve += msg.value;
    }

    function balanceOf(address who) public view returns (uint256) { return shares[who]; }

    function ownerOf_() public view returns (address) { return owner; }
}
