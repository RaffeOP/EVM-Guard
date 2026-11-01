pragma solidity 0.8.20;

contract Locker5210 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public shares;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        reserve += msg.value;
    }

    function ownerOf_() public view returns (address) { return owner; }
}
